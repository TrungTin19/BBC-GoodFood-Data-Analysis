# -*- coding: utf-8 -*-
"""
Offline EDA charts and summary for the BBC Good Food SQLite database.

The script reads local SQLite data only, writes charts under outputs/charts,
and writes machine-readable + Markdown summaries under outputs/reports.
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402

from config import DB_PATH  # noqa: E402
from parser import MAX_REASONABLE_DURATION_MINUTES, normalize_duration_minutes  # noqa: E402


REPORTS_DIR = ROOT_DIR / "outputs" / "reports"
CHARTS_DIR = ROOT_DIR / "outputs" / "charts"


def _ensure_dirs(reports_dir: Path, charts_dir: Path) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    charts_dir.mkdir(parents=True, exist_ok=True)


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


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


def _load_dataframe(conn: sqlite3.Connection, table_name: str) -> pd.DataFrame:
    if not _table_exists(conn, table_name):
        return pd.DataFrame()
    return pd.read_sql_query(f"SELECT * FROM {table_name}", conn)


def _save_rating_distribution(recipes: pd.DataFrame, charts_dir: Path) -> Tuple[Optional[str], str]:
    if "rating" not in recipes.columns:
        return None, "Rating column is not available."
    ratings = pd.to_numeric(recipes["rating"], errors="coerce").dropna()
    if ratings.empty:
        return None, "Rating data is empty."

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.histplot(ratings, bins=20, kde=True, color="#386cb0", ax=ax)
    ax.axvline(ratings.mean(), color="#d95f02", linestyle="--", label=f"Mean {ratings.mean():.2f}")
    ax.set_title("Rating Distribution")
    ax.set_xlabel("Rating")
    ax.set_ylabel("Recipe count")
    ax.legend()
    fig.tight_layout()
    path = charts_dir / "rating_distribution.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)

    skew_note = "Ratings are concentrated near the high end." if ratings.median() >= 4 else "Ratings are not strongly high-skewed."
    return str(path), f"The chart shows {len(ratings)} rated recipes. Median={ratings.median():.2f}, mean={ratings.mean():.2f}. {skew_note} Missing ratings are excluded."


def _save_top_ingredients(ingredients: pd.DataFrame, charts_dir: Path) -> Tuple[Optional[str], str]:
    if "ingredient" not in ingredients.columns:
        return None, "Ingredient column is not available."
    series = ingredients["ingredient"].dropna().astype(str).str.strip()
    series = series[series != ""]
    if series.empty:
        return None, "Ingredient data is empty."

    counts = series.value_counts().head(20)
    fig, ax = plt.subplots(figsize=(10, 7))
    sns.barplot(x=counts.values, y=counts.index, ax=ax, color="#4daf4a")
    ax.set_title("Top 20 Ingredients")
    ax.set_xlabel("Count")
    ax.set_ylabel("Ingredient")
    fig.tight_layout()
    path = charts_dir / "top_ingredients.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)

    top_item = counts.index[0]
    top_count = int(counts.iloc[0])
    return str(path), f"The chart ranks the 20 most frequent cleaned ingredients. `{top_item}` is most common with {top_count} appearances. Limitation: ingredient cleaning may merge or split synonyms imperfectly."


def _save_difficulty_distribution(recipes: pd.DataFrame, charts_dir: Path) -> Tuple[Optional[str], str]:
    if "difficulty" not in recipes.columns:
        return None, "Difficulty column is not available."
    values = recipes["difficulty"].fillna("Unknown").astype(str).str.strip()
    values = values.replace("", "Unknown")
    counts = values.value_counts()
    if counts.empty:
        return None, "Difficulty data is empty."

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(x=counts.index, y=counts.values, hue=counts.index, ax=ax, palette="viridis", legend=False)
    ax.set_title("Difficulty Distribution")
    ax.set_xlabel("Difficulty")
    ax.set_ylabel("Recipe count")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    path = charts_dir / "difficulty_distribution.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)

    dominant = counts.index[0]
    return str(path), f"The chart shows recipe difficulty categories. `{dominant}` is the dominant group. Limitation: missing or changed BBC labels are grouped as Unknown."


def _save_dietary_distribution(recipes: pd.DataFrame, charts_dir: Path) -> Tuple[Optional[str], str]:
    if "dietary_labels" not in recipes.columns:
        return None, "Dietary label column is not available."
    counter: Counter[str] = Counter()
    for value in recipes["dietary_labels"].dropna():
        for label in str(value).split(","):
            clean = label.strip()
            if clean:
                counter[clean] += 1
    if not counter:
        return None, "Dietary label data is empty."

    labels, counts = zip(*counter.most_common(20))
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(x=list(labels), y=list(counts), hue=list(labels), ax=ax, palette="Set2", legend=False)
    ax.set_title("Dietary Label Distribution")
    ax.set_xlabel("Dietary label")
    ax.set_ylabel("Recipe count")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    path = charts_dir / "dietary_distribution.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)

    return str(path), "The chart shows that dietary labels are multi-label and imbalanced. Limitation: labels come from site tags/keywords and may be noisy or incomplete."


def _save_cooking_time_distribution(
    recipes: pd.DataFrame,
    charts_dir: Path,
) -> Tuple[Optional[str], str, Dict[str, Any]]:
    available = [col for col in ["prep_time_min", "cook_time_min", "total_time_min", "total_time"] if col in recipes.columns]
    if not available:
        return None, "No cooking time columns are available.", {}

    time_frames = []
    quality: Dict[str, Any] = {}
    for col in available:
        values = pd.to_numeric(recipes[col], errors="coerce").dropna()
        valid_values = [normalize_duration_minutes(value) for value in values.tolist()]
        valid_values = [value for value in valid_values if value is not None]
        outlier_count = int((values > MAX_REASONABLE_DURATION_MINUTES).sum())
        invalid_count = int(len(values) - len(valid_values) - outlier_count)
        quality[col] = {
            "raw_count": int(len(values)),
            "valid_count": int(len(valid_values)),
            "invalid_count": invalid_count,
            "outlier_count": outlier_count,
            "threshold_minutes": MAX_REASONABLE_DURATION_MINUTES,
        }
        if valid_values:
            time_frames.append(pd.DataFrame({"minutes": valid_values, "type": col}))
    if not time_frames:
        return None, "Cooking time data is empty after filtering invalid/outlier values.", quality

    plot_df = pd.concat(time_frames, ignore_index=True)
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.histplot(data=plot_df, x="minutes", hue="type", bins=30, kde=True, ax=ax)
    ax.set_title("Cooking Time Distribution")
    ax.set_xlabel("Minutes")
    ax.set_ylabel("Recipe count")
    fig.tight_layout()
    path = charts_dir / "cooking_time_distribution.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)

    total_outliers = sum(item["outlier_count"] for item in quality.values())
    total_invalid = sum(item["invalid_count"] for item in quality.values())
    return (
        str(path),
        "The chart excludes invalid values and values above "
        f"{MAX_REASONABLE_DURATION_MINUTES} minutes so unrealistic outliers do not distort the distribution. "
        f"Excluded outliers: {total_outliers}; other invalid values: {total_invalid}. "
        "The threshold is one full day, which is generous for recipe prep/cook durations.",
        quality,
    )


def run_eda_analysis(
    db_path: str = DB_PATH,
    reports_dir: Optional[Path] = None,
    charts_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    target_reports = Path(reports_dir) if reports_dir is not None else REPORTS_DIR
    target_charts = Path(charts_dir) if charts_dir is not None else CHARTS_DIR
    _ensure_dirs(target_reports, target_charts)

    summary: Dict[str, Any] = {
        "database_path": str(db_path),
        "database_exists": Path(db_path).exists(),
        "status": "ok",
        "charts": {},
        "interpretations": {},
        "errors": [],
    }

    if not Path(db_path).exists():
        summary["status"] = "error"
        summary["errors"].append("Database file does not exist.")
    else:
        try:
            conn = _connect(db_path)
            recipes = _load_dataframe(conn, "recipes")
            ingredients = _load_dataframe(conn, "ingredients")
            conn.close()

            summary["row_counts"] = {
                "recipes": int(len(recipes)),
                "ingredients": int(len(ingredients)),
            }

            chart_functions = {
                "rating_distribution": lambda: _save_rating_distribution(recipes, target_charts),
                "top_ingredients": lambda: _save_top_ingredients(ingredients, target_charts),
                "difficulty_distribution": lambda: _save_difficulty_distribution(recipes, target_charts),
                "dietary_distribution": lambda: _save_dietary_distribution(recipes, target_charts),
            }
            for name, func in chart_functions.items():
                path, interpretation = func()
                summary["charts"][name] = path or "not_created"
                summary["interpretations"][name] = interpretation
            path, interpretation, time_quality = _save_cooking_time_distribution(recipes, target_charts)
            summary["charts"]["cooking_time_distribution"] = path or "not_created"
            summary["interpretations"]["cooking_time_distribution"] = interpretation
            summary["time_quality"] = time_quality
        except Exception as exc:  # EDA should report failures instead of crashing.
            summary["status"] = "error"
            summary["errors"].append(str(exc))

    json_path = target_reports / "eda_summary.json"
    md_path = target_reports / "eda_summary.md"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown_summary(summary, md_path)
    summary["output_files"] = {"json": str(json_path), "markdown": str(md_path)}
    return summary


def write_markdown_summary(summary: Dict[str, Any], path: Path) -> None:
    lines = [
        "# Offline EDA Summary",
        "",
        f"- Database: `{summary.get('database_path')}`",
        f"- Status: **{summary.get('status')}**",
        f"- Database exists: `{summary.get('database_exists')}`",
        "",
        "## Row Counts",
        "",
        "```json",
        json.dumps(summary.get("row_counts", {}), ensure_ascii=False, indent=2),
        "```",
        "",
        "## Time Quality Used For EDA",
        "",
        "```json",
        json.dumps(summary.get("time_quality", {}), ensure_ascii=False, indent=2),
        "```",
        "",
        "## Charts and Interpretation",
        "",
    ]

    charts = summary.get("charts", {})
    interpretations = summary.get("interpretations", {})
    for name in [
        "rating_distribution",
        "top_ingredients",
        "difficulty_distribution",
        "dietary_distribution",
        "cooking_time_distribution",
    ]:
        lines.extend(
            [
                f"### {name}",
                "",
                f"- Output: `{charts.get(name, 'not_created')}`",
                f"- Interpretation: {interpretations.get(name, 'not_available')}",
                "",
            ]
        )

    errors = summary.get("errors", [])
    if errors:
        lines.extend(["## Errors", ""])
        for error in errors:
            lines.append(f"- {error}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    summary = run_eda_analysis()
    print(f"EDA status: {summary['status']}")
    print(f"Wrote: {REPORTS_DIR / 'eda_summary.json'}")
    print(f"Wrote: {REPORTS_DIR / 'eda_summary.md'}")


if __name__ == "__main__":
    main()
