import json
import sqlite3

from ml_search import get_model_path, is_trusted_model_path
from scripts.offline_model_evaluation import evaluate_models


def _create_model_db(path):
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE recipes (
            recipe_id INTEGER PRIMARY KEY,
            title TEXT,
            raw_ingredients TEXT,
            dietary_labels TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE ingredients (
            id INTEGER PRIMARY KEY,
            recipe_id INTEGER,
            ingredient TEXT
        )
        """
    )

    rows = []
    for idx in range(1, 21):
        is_veg = idx % 2 == 0
        ingredients = "tofu tomato basil olive oil" if is_veg else "chicken garlic butter"
        labels = "Vegetarian" if is_veg else ""
        rows.append((idx, f"Recipe {idx}", ingredients, labels))
    conn.executemany(
        "INSERT INTO recipes (recipe_id, title, raw_ingredients, dietary_labels) VALUES (?, ?, ?, ?)",
        rows,
    )
    for recipe_id, _, raw_ingredients, _ in rows:
        for ingredient in raw_ingredients.split():
            conn.execute(
                "INSERT INTO ingredients (recipe_id, ingredient) VALUES (?, ?)",
                (recipe_id, ingredient),
            )
    conn.commit()
    conn.close()


def test_model_evaluation_creates_reports(tmp_path):
    db_path = tmp_path / "recipes.db"
    output_dir = tmp_path / "reports"
    _create_model_db(db_path)

    report = evaluate_models(str(db_path), output_dir=output_dir)

    assert report["status"] == "ok"
    assert report["search_index"]["status"] == "ok"
    assert report["classification"]["Vegetarian"]["status"] == "ok"
    assert (output_dir / "model_evaluation.json").exists()
    assert (output_dir / "model_evaluation.md").exists()

    payload = json.loads((output_dir / "model_evaluation.json").read_text(encoding="utf-8"))
    assert payload["classification"]["Vegetarian"]["models"]["nb"]["confusion_matrix"]


def test_model_evaluation_handles_tiny_or_missing_data(tmp_path):
    db_path = tmp_path / "tiny.db"
    output_dir = tmp_path / "reports"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE recipes (recipe_id INTEGER PRIMARY KEY, title TEXT, raw_ingredients TEXT, dietary_labels TEXT)"
    )
    conn.execute("INSERT INTO recipes VALUES (1, 'Only one', 'salt', '')")
    conn.commit()
    conn.close()

    report = evaluate_models(str(db_path), output_dir=output_dir)

    assert report["status"] == "ok"
    assert report["classification"]["Vegetarian"]["status"] == "skipped"
    assert (output_dir / "model_evaluation.json").exists()


def test_model_path_trust_check():
    trusted = get_model_path("nb", "Vegetarian")
    assert is_trusted_model_path(trusted)
    assert not is_trusted_model_path(r"C:\temp\evil.pkl")
