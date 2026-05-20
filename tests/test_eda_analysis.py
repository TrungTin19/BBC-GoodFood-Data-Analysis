import json
import sqlite3

from scripts.offline_eda_analysis import run_eda_analysis


def _create_eda_db(path):
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE recipes (
            recipe_id INTEGER PRIMARY KEY,
            title TEXT,
            rating REAL,
            prep_time_min INTEGER,
            cook_time_min INTEGER,
            difficulty TEXT,
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
    for idx in range(1, 8):
        conn.execute(
            """
            INSERT INTO recipes
                (recipe_id, title, rating, prep_time_min, cook_time_min, difficulty, dietary_labels)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                idx,
                f"Recipe {idx}",
                3.5 + idx * 0.1,
                10 + idx,
                20 + idx,
                "Easy" if idx % 2 else "More effort",
                "Vegetarian" if idx % 2 else "Gluten-free",
            ),
        )
        conn.execute(
            "INSERT INTO ingredients (recipe_id, ingredient) VALUES (?, ?)",
            (idx, "tomato" if idx % 2 else "garlic"),
        )
    conn.execute(
        """
        INSERT INTO recipes
            (recipe_id, title, rating, prep_time_min, cook_time_min, difficulty, dietary_labels)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (99, "Outlier time", 4.2, 176986657, -5, "Easy", "Vegetarian"),
    )
    conn.commit()
    conn.close()


def test_eda_analysis_creates_reports_and_charts(tmp_path):
    db_path = tmp_path / "recipes.db"
    reports_dir = tmp_path / "reports"
    charts_dir = tmp_path / "charts"
    _create_eda_db(db_path)

    summary = run_eda_analysis(str(db_path), reports_dir=reports_dir, charts_dir=charts_dir)

    assert summary["status"] == "ok"
    assert (reports_dir / "eda_summary.json").exists()
    assert (reports_dir / "eda_summary.md").exists()
    assert (charts_dir / "rating_distribution.png").exists()
    assert (charts_dir / "top_ingredients.png").exists()
    assert (charts_dir / "difficulty_distribution.png").exists()
    assert (charts_dir / "cooking_time_distribution.png").exists()

    payload = json.loads((reports_dir / "eda_summary.json").read_text(encoding="utf-8"))
    assert payload["charts"]["rating_distribution"].endswith("rating_distribution.png")
    assert payload["time_quality"]["prep_time_min"]["outlier_count"] == 1
    assert payload["time_quality"]["cook_time_min"]["invalid_count"] == 1


def test_eda_analysis_handles_missing_database(tmp_path):
    summary = run_eda_analysis(
        str(tmp_path / "missing.db"),
        reports_dir=tmp_path / "reports",
        charts_dir=tmp_path / "charts",
    )

    assert summary["status"] == "error"
    assert (tmp_path / "reports" / "eda_summary.json").exists()
