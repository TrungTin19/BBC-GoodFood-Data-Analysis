# -*- coding: utf-8 -*-
"""
Offline TF-IDF search and dietary-label model evaluation.

This script uses only the local SQLite database. It writes JSON + Markdown
reports and degrades gracefully when the dataset is too small or labels are
missing/imbalanced.
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

import pandas as pd  # noqa: E402
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import (  # noqa: E402
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.metrics.pairwise import cosine_similarity  # noqa: E402
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split  # noqa: E402
from sklearn.naive_bayes import MultinomialNB  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402

from config import DB_PATH, DIETARY_LABELS, RANDOM_STATE, TEST_SIZE  # noqa: E402


REPORTS_DIR = ROOT_DIR / "outputs" / "reports"


def _ensure_output_dir(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)


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


def _load_recipe_features(db_path: str) -> Tuple[pd.DataFrame, List[str]]:
    conn = _connect(db_path)
    try:
        if not _table_exists(conn, "recipes"):
            return pd.DataFrame(), []

        recipe_cols = _columns(conn, "recipes")
        ingredient_cols = _columns(conn, "ingredients")
        if "recipe_id" in recipe_cols and "recipe_id" in ingredient_cols and "ingredient" in ingredient_cols:
            query = """
                SELECT r.recipe_id, r.title, r.raw_ingredients, r.dietary_labels,
                       GROUP_CONCAT(i.ingredient, ' ') AS ingredients_text
                FROM recipes r
                LEFT JOIN ingredients i ON r.recipe_id = i.recipe_id
                GROUP BY r.recipe_id
                ORDER BY r.recipe_id
            """
        else:
            select_cols = ["recipe_id", "title", "raw_ingredients", "dietary_labels"]
            available = [col for col in select_cols if col in recipe_cols]
            query = f"SELECT {', '.join(available)} FROM recipes ORDER BY {available[0]}"
        df = pd.read_sql_query(query, conn)
        return df, recipe_cols
    finally:
        conn.close()


def evaluate_search_index(df: pd.DataFrame) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "status": "not_evaluated",
        "reason": "",
        "sample_query": None,
        "results": [],
    }
    if df.empty:
        result["reason"] = "No recipes available."
        return result

    text_col = "ingredients_text" if "ingredients_text" in df.columns else "raw_ingredients"
    if text_col not in df.columns:
        result["reason"] = "No ingredient text column available."
        return result

    corpus = df[text_col].fillna("").astype(str)
    corpus = corpus[corpus.str.strip() != ""]
    if corpus.empty:
        result["reason"] = "Ingredient corpus is empty."
        return result

    vectorizer = TfidfVectorizer(stop_words="english", max_features=5000, ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(df[text_col].fillna("").astype(str).tolist())
    feature_count = len(vectorizer.get_feature_names_out())

    words = " ".join(corpus.head(50).tolist()).split()
    common = [word for word, _ in Counter(words).most_common(3)]
    sample_query = " ".join(common) if common else "chicken garlic"
    query_vec = vectorizer.transform([sample_query])
    similarities = cosine_similarity(query_vec, matrix).flatten()

    top_indices = similarities.argsort()[::-1][:5]
    top_results = []
    for idx in top_indices:
        if similarities[idx] <= 0:
            continue
        row = df.iloc[int(idx)]
        top_results.append(
            {
                "title": str(row.get("title", "")),
                "similarity": round(float(similarities[idx]), 4),
            }
        )

    result.update(
        {
            "status": "ok",
            "recipe_count": int(len(df)),
            "feature_count": int(feature_count),
            "sample_query": sample_query,
            "results": top_results,
        }
    )
    return result


def _can_classify(df: pd.DataFrame, label: str) -> Tuple[bool, str, pd.Series, pd.Series]:
    if "raw_ingredients" not in df.columns or "dietary_labels" not in df.columns:
        return False, "raw_ingredients or dietary_labels column is missing.", pd.Series(dtype=str), pd.Series(dtype=int)

    data = df[["raw_ingredients", "dietary_labels"]].copy()
    data["raw_ingredients"] = data["raw_ingredients"].fillna("").astype(str)
    data = data[data["raw_ingredients"].str.strip() != ""]
    if len(data) < 10:
        return False, "Fewer than 10 labeled ingredient samples.", pd.Series(dtype=str), pd.Series(dtype=int)

    y = data["dietary_labels"].fillna("").astype(str).apply(
        lambda value: int(
            any(label.lower() == token.strip().lower() for token in value.split(","))
        )
    )
    counts = y.value_counts().to_dict()
    if counts.get(1, 0) < 2 or counts.get(0, 0) < 2:
        return False, f"Not enough positive/negative samples: {counts}.", pd.Series(dtype=str), pd.Series(dtype=int)

    return True, "ok", data["raw_ingredients"], y


def _model_pipeline(model_type: str) -> Pipeline:
    if model_type == "logistic":
        classifier = LogisticRegression(random_state=RANDOM_STATE, max_iter=1000)
    else:
        classifier = MultinomialNB()
    return Pipeline(
        [
            (
                "vectorizer",
                CountVectorizer(stop_words="english", max_features=5000, ngram_range=(1, 2)),
            ),
            ("classifier", classifier),
        ]
    )


def evaluate_classification(df: pd.DataFrame) -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    for label in DIETARY_LABELS:
        can_run, reason, X, y = _can_classify(df, label)
        if not can_run:
            results[label] = {"status": "skipped", "reason": reason}
            continue

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=TEST_SIZE,
            random_state=RANDOM_STATE,
            stratify=y,
        )
        min_train_class = int(y_train.value_counts().min())
        label_results: Dict[str, Any] = {
            "status": "ok",
            "total_samples": int(len(X)),
            "positive_count": int(y.sum()),
            "negative_count": int(len(y) - y.sum()),
            "train_size": int(len(X_train)),
            "test_size": int(len(X_test)),
            "models": {},
        }

        for model_type in ["nb", "logistic"]:
            pipeline = _model_pipeline(model_type)
            pipeline.fit(X_train, y_train)
            y_pred = pipeline.predict(X_test)

            metrics = {
                "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
                "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
                "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
                "f1": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
                "confusion_matrix": confusion_matrix(y_test, y_pred, labels=[0, 1]).tolist(),
            }

            if min_train_class >= 2:
                cv_folds = min(5, min_train_class)
                cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=RANDOM_STATE)
                cv_scores = cross_val_score(pipeline, X_train, y_train, cv=cv)
                metrics["cv_accuracy_mean"] = round(float(cv_scores.mean()), 4)
                metrics["cv_folds"] = int(cv_folds)
            else:
                metrics["cv_accuracy_mean"] = "not_available"
                metrics["cv_folds"] = 0

            label_results["models"][model_type] = metrics
        results[label] = label_results

    return results


def evaluate_models(db_path: str = DB_PATH, output_dir: Optional[Path] = None) -> Dict[str, Any]:
    target_dir = Path(output_dir) if output_dir is not None else REPORTS_DIR
    _ensure_output_dir(target_dir)

    report: Dict[str, Any] = {
        "database_path": str(db_path),
        "database_exists": Path(db_path).exists(),
        "status": "ok",
        "search_index": {},
        "classification": {},
        "limitations": [
            "Dietary labels are noisy because they come from source tags/keywords.",
            "Class imbalance can make accuracy look better than recall/F1.",
            "The dataset may be small or stale if data/ is ignored in a fresh clone.",
            "No direct data leakage from dietary_labels into features is used here, but recipe titles/descriptions are intentionally not used to reduce leakage risk.",
        ],
        "errors": [],
    }

    if not Path(db_path).exists():
        report["status"] = "error"
        report["errors"].append("Database file does not exist.")
    else:
        try:
            df, _ = _load_recipe_features(db_path)
            report["search_index"] = evaluate_search_index(df)
            report["classification"] = evaluate_classification(df)
        except Exception as exc:
            report["status"] = "error"
            report["errors"].append(str(exc))

    json_path = target_dir / "model_evaluation.json"
    md_path = target_dir / "model_evaluation.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown_report(report, md_path)
    report["output_files"] = {"json": str(json_path), "markdown": str(md_path)}
    return report


def write_markdown_report(report: Dict[str, Any], path: Path) -> None:
    lines = [
        "# Offline Model Evaluation",
        "",
        f"- Database: `{report.get('database_path')}`",
        f"- Status: **{report.get('status')}**",
        f"- Database exists: `{report.get('database_exists')}`",
        "",
        "## Search Index",
        "",
        "```json",
        json.dumps(report.get("search_index", {}), ensure_ascii=False, indent=2),
        "```",
        "",
        "## Classification Metrics",
        "",
    ]

    classification = report.get("classification", {})
    for label, result in classification.items():
        lines.extend([f"### {label}", "", "```json"])
        lines.append(json.dumps(result, ensure_ascii=False, indent=2))
        lines.extend(["```", ""])

    lines.extend(["## Limitations", ""])
    for item in report.get("limitations", []):
        lines.append(f"- {item}")

    errors = report.get("errors", [])
    if errors:
        lines.extend(["", "## Errors", ""])
        for error in errors:
            lines.append(f"- {error}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    report = evaluate_models()
    print(f"Model evaluation status: {report['status']}")
    print(f"Wrote: {REPORTS_DIR / 'model_evaluation.json'}")
    print(f"Wrote: {REPORTS_DIR / 'model_evaluation.md'}")


if __name__ == "__main__":
    main()
