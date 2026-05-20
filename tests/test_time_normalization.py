import sqlite3

from parser import normalize_duration_minutes
from scripts.offline_data_quality_report import generate_data_quality_report
from scripts.offline_eda_analysis import run_eda_analysis


def test_normalize_duration_minutes_common_inputs():
    assert normalize_duration_minutes("10 mins") == 10
    assert normalize_duration_minutes("1 hr") == 60
    assert normalize_duration_minutes("1 hr 30 mins") == 90
    assert normalize_duration_minutes("PT1H30M") == 90
    assert normalize_duration_minutes(45) == 45


def test_normalize_duration_minutes_invalid_inputs():
    assert normalize_duration_minutes(-5) is None
    assert normalize_duration_minutes(176986657) is None
    assert normalize_duration_minutes(None) is None
    assert normalize_duration_minutes("") is None


def _create_outlier_db(path):
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE recipes (
            recipe_id INTEGER PRIMARY KEY,
            title TEXT,
            url TEXT,
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
    conn.executemany(
        """
        INSERT INTO recipes
            (recipe_id, title, url, rating, prep_time_min, cook_time_min, difficulty, dietary_labels)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (1, "Valid", "https://example.com/valid", 4.5, 10, 20, "Easy", "Vegetarian"),
            (2, "Huge", "https://example.com/huge", 4.0, 176986657, 176986657, "Easy", ""),
            (3, "Negative", "https://example.com/negative", 3.0, -5, -1, "Easy", ""),
        ],
    )
    conn.executemany(
        "INSERT INTO ingredients (recipe_id, ingredient) VALUES (?, ?)",
        [(1, "tomato"), (2, "garlic"), (3, "onion")],
    )
    conn.commit()
    conn.close()


def test_data_quality_report_handles_time_outliers(tmp_path):
    db_path = tmp_path / "recipes.db"
    output_dir = tmp_path / "reports"
    _create_outlier_db(db_path)

    report = generate_data_quality_report(str(db_path), output_dir=output_dir)

    assert report["status"] == "ok"
    assert report["time_quality"]["prep_time_min"]["valid_time_count"] == 1
    assert report["time_quality"]["prep_time_min"]["outlier_time_count"] == 1
    assert report["time_quality"]["prep_time_min"]["invalid_time_count"] == 1
    assert (output_dir / "data_quality_report.json").exists()


def test_eda_analysis_handles_time_outliers(tmp_path):
    db_path = tmp_path / "recipes.db"
    reports_dir = tmp_path / "reports"
    charts_dir = tmp_path / "charts"
    _create_outlier_db(db_path)

    summary = run_eda_analysis(str(db_path), reports_dir=reports_dir, charts_dir=charts_dir)

    assert summary["status"] == "ok"
    assert summary["time_quality"]["prep_time_min"]["outlier_count"] == 1
    assert summary["time_quality"]["prep_time_min"]["invalid_count"] == 1
    assert (charts_dir / "cooking_time_distribution.png").exists()
