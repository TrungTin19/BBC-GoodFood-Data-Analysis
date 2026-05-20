# -*- coding: utf-8 -*-
"""
Offline data quality report for the BBC Good Food SQLite database.

This script never crawls the web. It reads the configured SQLite database,
handles missing tables/columns defensively, and writes JSON + Markdown reports.
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path
from statistics import mean, median
from typing import Any, Dict, Iterable, List, Optional

import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import DB_PATH  # noqa: E402
from parser import MAX_REASONABLE_DURATION_MINUTES, normalize_duration_minutes  # noqa: E402


REPORTS_DIR = ROOT_DIR / "outputs" / "reports"


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_output_dir(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


def _columns(conn: sqlite3.Connection, table_name: str) -> List[str]:
    if not _table_exists(conn, table_name):
        return []
    return [row["name"] for row in conn.execute(f"PRAGMA table_info({table_name})")]


def _count_rows(conn: sqlite3.Connection, table_name: str) -> Any:
    if not _table_exists(conn, table_name):
        return "not_available"
    return int(conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0])


def _missing_count(conn: sqlite3.Connection, table_name: str, column: str) -> Any:
    cols = _columns(conn, table_name)
    if column not in cols:
        return "not_available"
    row = conn.execute(
        f"""
        SELECT COUNT(*)
        FROM {table_name}
        WHERE {column} IS NULL OR TRIM(CAST({column} AS TEXT)) = ''
        """
    ).fetchone()
    return int(row[0])


def _duplicate_extra_count(conn: sqlite3.Connection, table_name: str, column: str) -> Any:
    cols = _columns(conn, table_name)
    if column not in cols:
        return "not_available"
    row = conn.execute(
        f"""
        SELECT COALESCE(SUM(cnt - 1), 0)
        FROM (
            SELECT {column}, COUNT(*) AS cnt
            FROM {table_name}
            WHERE {column} IS NOT NULL AND TRIM(CAST({column} AS TEXT)) != ''
            GROUP BY {column}
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()
    return int(row[0] or 0)


def _numeric_values(
    conn: sqlite3.Connection,
    table_name: str,
    column: str,
    valid_duration_only: bool = False,
) -> List[float]:
    if column not in _columns(conn, table_name):
        return []
    rows = conn.execute(
        f"SELECT {column} FROM {table_name} WHERE {column} IS NOT NULL"
    ).fetchall()
    values: List[float] = []
    for row in rows:
        try:
            value = float(row[0])
        except (TypeError, ValueError):
            continue
        if valid_duration_only and normalize_duration_minutes(value) is None:
            continue
        values.append(value)
    return values


def _numeric_stats(values: Iterable[float]) -> Any:
    vals = list(values)
    if not vals:
        return "not_available"
    return {
        "count": len(vals),
        "mean": round(mean(vals), 4),
        "median": round(median(vals), 4),
        "min": min(vals),
        "max": max(vals),
    }


def _top_ingredients(conn: sqlite3.Connection, limit: int = 20) -> Any:
    cols = _columns(conn, "ingredients")
    if "ingredient" not in cols:
        return "not_available"
    rows = conn.execute(
        """
        SELECT ingredient, COUNT(*) AS count
        FROM ingredients
        WHERE ingredient IS NOT NULL AND TRIM(ingredient) != ''
        GROUP BY ingredient
        ORDER BY count DESC, ingredient ASC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [{"ingredient": row["ingredient"], "count": int(row["count"])} for row in rows]


def _distribution(conn: sqlite3.Connection, table_name: str, column: str) -> Any:
    if column not in _columns(conn, table_name):
        return "not_available"
    rows = conn.execute(
        f"""
        SELECT COALESCE(NULLIF(TRIM(CAST({column} AS TEXT)), ''), 'Unknown') AS value,
               COUNT(*) AS count
        FROM {table_name}
        GROUP BY value
        ORDER BY count DESC, value ASC
        """
    ).fetchall()
    return {str(row["value"]): int(row["count"]) for row in rows}


def _dietary_distribution(conn: sqlite3.Connection) -> Any:
    if "dietary_labels" not in _columns(conn, "recipes"):
        return "not_available"
    rows = conn.execute(
        "SELECT dietary_labels FROM recipes WHERE dietary_labels IS NOT NULL"
    ).fetchall()
    counter: Counter[str] = Counter()
    for row in rows:
        for label in str(row["dietary_labels"]).split(","):
            clean = label.strip()
            if clean:
                counter[clean] += 1
    return dict(counter.most_common()) if counter else {}


def _recipes_without_ingredients(conn: sqlite3.Connection) -> Any:
    recipe_cols = _columns(conn, "recipes")
    ingredient_cols = _columns(conn, "ingredients")
    if "recipe_id" not in recipe_cols or "recipe_id" not in ingredient_cols:
        return "not_available"
    row = conn.execute(
        """
        SELECT COUNT(*)
        FROM recipes r
        LEFT JOIN ingredients i ON r.recipe_id = i.recipe_id
        WHERE i.recipe_id IS NULL
        """
    ).fetchone()
    return int(row[0])


def _time_quality(conn: sqlite3.Connection, time_columns: List[str]) -> Dict[str, Any]:
    quality: Dict[str, Any] = {}
    recipe_cols = _columns(conn, "recipes")
    for col in time_columns:
        if col not in recipe_cols:
            quality[col] = "not_available"
            continue
        rows = conn.execute(
            f"""
            SELECT recipe_id, title, url, {col} AS value
            FROM recipes
            WHERE {col} IS NOT NULL
            """
        ).fetchall()

        valid_count = invalid_count = outlier_count = 0
        max_valid = None
        invalid_records = []
        outlier_records = []
        for row in rows:
            raw_value = row["value"]
            normalized = normalize_duration_minutes(raw_value)
            record = {
                "recipe_id": row["recipe_id"],
                "title": row["title"],
                "url": row["url"],
                "value": raw_value,
            }
            try:
                numeric = float(raw_value)
            except (TypeError, ValueError):
                numeric = None

            if normalized is not None:
                valid_count += 1
                max_valid = normalized if max_valid is None else max(max_valid, normalized)
            elif numeric is not None and numeric > MAX_REASONABLE_DURATION_MINUTES:
                outlier_count += 1
                if len(outlier_records) < 25:
                    outlier_records.append(record)
            else:
                invalid_count += 1
                if len(invalid_records) < 25:
                    invalid_records.append(record)

        top_invalid_or_outlier = [
            {
                **item,
                "reason": f">{MAX_REASONABLE_DURATION_MINUTES} minutes",
            }
            for item in outlier_records
        ] + [
            {
                **item,
                "reason": "negative_or_non_numeric",
            }
            for item in invalid_records
        ]

        quality[col] = {
            "valid_time_count": valid_count,
            "invalid_time_count": invalid_count,
            "outlier_time_count": outlier_count,
            "max_valid_time": max_valid if max_valid is not None else "not_available",
            "threshold_minutes": MAX_REASONABLE_DURATION_MINUTES,
            "top_invalid_or_outlier_records": top_invalid_or_outlier[:25],
        }
    return quality


def collect_data_quality_metrics(db_path: str = DB_PATH) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "database_path": str(db_path),
        "database_exists": Path(db_path).exists(),
        "status": "ok",
        "errors": [],
    }

    if not Path(db_path).exists():
        report["status"] = "error"
        report["errors"].append("Database file does not exist.")
        return report

    try:
        conn = _connect(db_path)
    except sqlite3.Error as exc:
        report["status"] = "error"
        report["errors"].append(f"Cannot open database: {exc}")
        return report

    try:
        recipe_cols = _columns(conn, "recipes")
        ingredient_cols = _columns(conn, "ingredients")
        time_columns = [
            col for col in ["prep_time_min", "cook_time_min", "total_time_min", "total_time"]
            if col in recipe_cols
        ]

        report.update(
            {
                "schema": {
                    "recipes_columns": recipe_cols or "not_available",
                    "ingredients_columns": ingredient_cols or "not_available",
                },
                "totals": {
                    "recipes": _count_rows(conn, "recipes"),
                    "ingredients": _count_rows(conn, "ingredients"),
                },
                "missing": {
                    "title": _missing_count(conn, "recipes", "title"),
                    "url": _missing_count(conn, "recipes", "url"),
                    "rating": _missing_count(conn, "recipes", "rating"),
                    "prep_time_min": _missing_count(conn, "recipes", "prep_time_min"),
                    "cook_time_min": _missing_count(conn, "recipes", "cook_time_min"),
                    "total_time": _missing_count(conn, "recipes", "total_time"),
                    "total_time_min": _missing_count(conn, "recipes", "total_time_min"),
                },
                "duplicates": {
                    "url_extra_rows": _duplicate_extra_count(conn, "recipes", "url"),
                    "title_extra_rows": _duplicate_extra_count(conn, "recipes", "title"),
                },
                "recipes_without_ingredients": _recipes_without_ingredients(conn),
                "top_20_ingredients": _top_ingredients(conn, 20),
                "difficulty_distribution": _distribution(conn, "recipes", "difficulty"),
                "dietary_label_distribution": _dietary_distribution(conn),
                "rating_stats": _numeric_stats(_numeric_values(conn, "recipes", "rating")),
                "time_stats_raw": {
                    col: _numeric_stats(_numeric_values(conn, "recipes", col))
                    for col in time_columns
                }
                if time_columns
                else "not_available",
                "time_stats_valid_only": {
                    col: _numeric_stats(
                        _numeric_values(conn, "recipes", col, valid_duration_only=True)
                    )
                    for col in time_columns
                }
                if time_columns
                else "not_available",
                "time_quality": _time_quality(conn, time_columns) if time_columns else "not_available",
            }
        )
    except sqlite3.Error as exc:
        report["status"] = "error"
        report["errors"].append(f"SQLite error while collecting metrics: {exc}")
    finally:
        conn.close()

    return report


def _format_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, indent=2)
    return str(value)


def write_markdown_report(report: Dict[str, Any], path: Path) -> None:
    lines = [
        "# Data Quality Report",
        "",
        f"- Database: `{report.get('database_path')}`",
        f"- Status: **{report.get('status')}**",
        f"- Database exists: `{report.get('database_exists')}`",
        "",
        "## Totals",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]
    totals = report.get("totals", {})
    if isinstance(totals, dict):
        for key, value in totals.items():
            lines.append(f"| {key} | {value} |")

    lines.extend(["", "## Missing Values", "", "| Field | Missing count |", "|---|---:|"])
    missing = report.get("missing", {})
    if isinstance(missing, dict):
        for key, value in missing.items():
            lines.append(f"| {key} | {value} |")

    lines.extend(["", "## Duplicate Checks", "", "| Field | Extra duplicate rows |", "|---|---:|"])
    duplicates = report.get("duplicates", {})
    if isinstance(duplicates, dict):
        for key, value in duplicates.items():
            lines.append(f"| {key} | {value} |")

    lines.extend(
        [
            "",
            "## Ingredients and Labels",
            "",
            f"- Recipes without ingredients: `{report.get('recipes_without_ingredients')}`",
            "",
            "### Top 20 Ingredients",
            "",
            "| Ingredient | Count |",
            "|---|---:|",
        ]
    )
    top_ingredients = report.get("top_20_ingredients")
    if isinstance(top_ingredients, list):
        for item in top_ingredients:
            lines.append(f"| {item['ingredient']} | {item['count']} |")
    else:
        lines.append(f"| not_available | {top_ingredients} |")

    lines.extend(
        [
            "",
            "## Rating and Time Statistics",
            "",
            "### Rating",
            "",
            "```json",
            _format_value(report.get("rating_stats")),
            "```",
            "",
            "### Time",
            "",
            "Raw values include invalid/outlier records. Valid-only values keep 0..1440 minutes.",
            "",
            "#### Raw Time Stats",
            "",
            "```json",
            _format_value(report.get("time_stats_raw")),
            "```",
            "",
            "#### Valid-Only Time Stats",
            "",
            "```json",
            _format_value(report.get("time_stats_valid_only")),
            "```",
            "",
            "### Time Quality",
            "",
            "```json",
            _format_value(report.get("time_quality")),
            "```",
            "",
            "## Distributions",
            "",
            "### Difficulty",
            "",
            "```json",
            _format_value(report.get("difficulty_distribution")),
            "```",
            "",
            "### Dietary Labels",
            "",
            "```json",
            _format_value(report.get("dietary_label_distribution")),
            "```",
        ]
    )

    errors = report.get("errors", [])
    if errors:
        lines.extend(["", "## Errors", ""])
        for error in errors:
            lines.append(f"- {error}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_data_quality_report(
    db_path: str = DB_PATH,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    target_dir = Path(output_dir) if output_dir is not None else REPORTS_DIR
    _ensure_output_dir(target_dir)
    report = collect_data_quality_metrics(db_path)

    json_path = target_dir / "data_quality_report.json"
    md_path = target_dir / "data_quality_report.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown_report(report, md_path)

    report["output_files"] = {
        "json": str(json_path),
        "markdown": str(md_path),
    }
    return report


def main() -> None:
    report = generate_data_quality_report()
    print(f"Data quality report status: {report['status']}")
    print(f"Wrote: {REPORTS_DIR / 'data_quality_report.json'}")
    print(f"Wrote: {REPORTS_DIR / 'data_quality_report.md'}")


if __name__ == "__main__":
    main()
