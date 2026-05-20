import json
import sqlite3

from scripts.offline_data_quality_report import generate_data_quality_report


def _create_quality_db(path):
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE recipes (
            recipe_id INTEGER PRIMARY KEY,
            title TEXT,
            url TEXT,
            prep_time_min INTEGER,
            cook_time_min INTEGER,
            rating REAL,
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
    conn.executemany(
        """
        INSERT INTO recipes
            (recipe_id, title, url, prep_time_min, cook_time_min, rating, difficulty, dietary_labels)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (1, "Tomato Pasta", "https://example.com/a", 10, 20, 4.5, "Easy", "Vegetarian"),
            (2, "Tomato Pasta", "https://example.com/b", None, 400, None, "Easy", ""),
            (3, "", "https://example.com/b", 5, -1, 3.0, None, "Vegan, Vegetarian"),
            (4, "Huge Time", "https://example.com/c", 176986657, 176986657, 4.0, "Easy", ""),
        ],
    )
    conn.executemany(
        "INSERT INTO ingredients (recipe_id, ingredient) VALUES (?, ?)",
        [(1, "tomato"), (1, "pasta"), (2, "tomato")],
    )
    conn.commit()
    conn.close()


def test_data_quality_report_creates_json_and_markdown(tmp_path):
    db_path = tmp_path / "recipes.db"
    output_dir = tmp_path / "reports"
    _create_quality_db(db_path)

    report = generate_data_quality_report(str(db_path), output_dir=output_dir)

    json_path = output_dir / "data_quality_report.json"
    md_path = output_dir / "data_quality_report.md"
    assert report["status"] == "ok"
    assert json_path.exists()
    assert md_path.exists()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["totals"]["recipes"] == 4
    assert payload["missing"]["title"] == 1
    assert payload["duplicates"]["url_extra_rows"] == 1
    assert payload["recipes_without_ingredients"] == 2
    assert payload["time_quality"]["prep_time_min"]["outlier_time_count"] == 1
    assert payload["time_quality"]["cook_time_min"]["outlier_time_count"] == 1
    assert payload["time_quality"]["cook_time_min"]["invalid_time_count"] == 1


def test_data_quality_report_handles_missing_schema(tmp_path):
    db_path = tmp_path / "minimal.db"
    output_dir = tmp_path / "reports"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE recipes (recipe_id INTEGER PRIMARY KEY, title TEXT)")
    conn.commit()
    conn.close()

    report = generate_data_quality_report(str(db_path), output_dir=output_dir)

    assert report["status"] == "ok"
    assert report["missing"]["url"] == "not_available"
    assert (output_dir / "data_quality_report.json").exists()
