# -*- coding: utf-8 -*-
"""
test_all.py - Kiểm tra toàn diện tất cả module trong BBC Good Food Crawler
=============================================================================
Chạy: python -m pytest test_all.py -v
Hoặc: python test_all.py

Bao gồm:
  1. Unit tests cho parse, database, ML
  2. Integration tests (pipeline mini)
  3. Edge cases
  4. Kiểm tra các tính năng mới
"""

import json
import os
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parser import (
    parse_time_to_minutes, clean_ingredient,
    _parse_iso_duration,
)
import database


# ============================================================================
# HỖ TRỢ: Tạo DB tạm và override đường dẫn
# ============================================================================
def _make_temp_db():
    """Tạo file DB tạm, trả về (fd, path)."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    return db_fd, db_path


def _use_db(db_path):
    """Override DB_PATH trong module database (dùng connection mới)."""
    database.DB_PATH = db_path


def _restore_db(original_path):
    """Khôi phục DB_PATH gốc."""
    database.DB_PATH = original_path


# ============================================================================
# 1. TEST PARSE - parse_time_to_minutes
# ============================================================================
class TestParseTimeToMinutes(unittest.TestCase):
    """Kiểm tra parse_time_to_minutes trả None thay vì 0 khi parse thất bại."""

    def test_standard_formats(self):
        self.assertEqual(parse_time_to_minutes("1 hr 20 mins"), 80)
        self.assertEqual(parse_time_to_minutes("2 hours 30 minutes"), 150)
        self.assertEqual(parse_time_to_minutes("45 mins"), 45)

    def test_only_hours(self):
        self.assertEqual(parse_time_to_minutes("2 hr"), 120)
        self.assertEqual(parse_time_to_minutes("1 hour"), 60)

    def test_only_minutes(self):
        self.assertEqual(parse_time_to_minutes("30 mins"), 30)
        self.assertEqual(parse_time_to_minutes("45 minutes"), 45)

    def test_none_input(self):
        self.assertIsNone(parse_time_to_minutes(None))

    def test_empty_string(self):
        self.assertIsNone(parse_time_to_minutes(""))
        self.assertIsNone(parse_time_to_minutes("   "))

    def test_no_numbers(self):
        self.assertIsNone(parse_time_to_minutes("N/A"))
        self.assertIsNone(parse_time_to_minutes("unknown"))

    def test_zero_minutes(self):
        """Sửa bug: '0 minutes' -> 0 (không phải None)."""
        self.assertEqual(parse_time_to_minutes("0 minutes"), 0)
        self.assertEqual(parse_time_to_minutes("0 mins"), 0)

    def test_plain_number(self):
        self.assertEqual(parse_time_to_minutes("45"), 45)

    def test_iso_duration(self):
        self.assertEqual(_parse_iso_duration("PT1H30M"), 90)
        self.assertEqual(_parse_iso_duration("PT45M"), 45)
        self.assertEqual(_parse_iso_duration("PT2H"), 120)

    def test_iso_duration_none(self):
        self.assertIsNone(_parse_iso_duration(None))
        self.assertIsNone(_parse_iso_duration(""))
        self.assertIsNone(_parse_iso_duration("PT"))

    def test_iso_duration_zero(self):
        """Sửa bug: 'PT0M' → 0 (không phải None). Duration hợp lệ bằng 0."""
        self.assertEqual(_parse_iso_duration("PT0M"), 0)
        self.assertEqual(_parse_iso_duration("PT0H0M"), 0)
        self.assertEqual(_parse_iso_duration("PT0H"), 0)


# ============================================================================
# 2. TEST PARSE - clean_ingredient
# ============================================================================
class TestCleanIngredient(unittest.TestCase):
    """Kiểm tra clean_ingredient loại bỏ số lượng, đơn vị, hướng dẫn."""

    def test_standard_ingredient(self):
        result = clean_ingredient("200g skinless chicken breasts, sliced")
        self.assertIn("skinless chicken breasts", result)
        self.assertNotIn("200g", result)

    def test_with_parentheses(self):
        result = clean_ingredient("1 tbsp olive oil (extra virgin)")
        self.assertNotIn("extra virgin", result)

    def test_unicode_fractions(self):
        result = clean_ingredient("1/2 cup milk")
        self.assertIn("milk", result)

    def test_no_quantity(self):
        result = clean_ingredient("salt and pepper")
        self.assertIn("salt and pepper", result)

    def test_empty_string(self):
        self.assertEqual(clean_ingredient(""), "")

    def test_cloves_unit(self):
        result = clean_ingredient("2 cloves garlic")
        self.assertIn("garlic", result)

    def test_x_prefix_preserved(self):
        """Sửa bug: nguyên liệu bắt đầu bằng 'x' không bị cắt sai."""
        # Trước khi sửa: 'x' nằm trong units → cắt thành 'ylitol'
        result = clean_ingredient("xylitol")
        self.assertIn("xylitol", result)

    def test_2x_pattern(self):
        """Pattern '2 x chicken' vẫn hoạt động (loại bỏ '2' nhưng giữ 'chicken')."""
        result = clean_ingredient("2 x chicken breasts")
        # Số '2' bị loại, 'x' giữ lại nhưng bị loại bởi regex ký tự đặc biệt đầu
        self.assertIn("chicken", result)


# ============================================================================
# 3. TEST DB - create_tables, insert_recipe, chống trùng
# ============================================================================
class TestDatabase(unittest.TestCase):
    """Kiểm tra database operations và chống trùng URL."""

    def setUp(self):
        self.db_fd, self.db_path = _make_temp_db()
        self.original_db_path = database.DB_PATH
        _use_db(self.db_path)
        database.create_tables()

    def tearDown(self):
        _restore_db(self.original_db_path)
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_create_tables(self):
        """create_tables tạo đúng 2 bảng."""
        conn = database.get_connection()
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        table_names = [t["name"] for t in tables]
        conn.close()
        self.assertIn("recipes", table_names)
        self.assertIn("ingredients", table_names)

    def test_insert_recipe_success(self):
        recipe_data = {
            "title": "Test Recipe",
            "url": "https://example.com/test",
            "prep_time_min": 15,
            "cook_time_min": 30,
            "difficulty": "Easy",
            "rating": 4.5,
            "review_count": 100,
            "dietary_labels": "Vegetarian",
            "raw_ingredients": "chicken; onion; garlic",
            "instructions": "Step 1: Cook",
            "description": "Test desc",
            "image_url": "https://example.com/img.jpg",
            "clean_ingredients": ["chicken", "onion", "garlic"],
        }
        result = database.insert_recipe(recipe_data)
        self.assertIsNotNone(result)
        self.assertEqual(database.get_recipe_count(), 1)

    def test_insert_recipe_duplicate(self):
        recipe_data = {
            "title": "Test Recipe",
            "url": "https://example.com/test",
            "clean_ingredients": ["chicken"],
        }
        # Lần 1: thành công
        self.assertIsNotNone(database.insert_recipe(recipe_data))
        # Lần 2: trùng URL -> None
        recipe_data["title"] = "Duplicate"
        self.assertIsNone(database.insert_recipe(recipe_data))
        self.assertEqual(database.get_recipe_count(), 1)

    def test_get_all_generic_query(self):
        """Test get_all() generic query."""
        recipe_data = {
            "title": "Test",
            "url": "https://example.com/1",
            "clean_ingredients": ["a"],
        }
        database.insert_recipe(recipe_data)
        results = database.get_all("SELECT * FROM recipes")
        self.assertEqual(len(results), 1)

    def test_get_recipe_by_id(self):
        recipe_data = {
            "title": "Test",
            "url": "https://example.com/1",
            "clean_ingredients": ["a", "b"],
        }
        rid = database.insert_recipe(recipe_data)
        self.assertIsNotNone(rid)
        recipe = database.get_recipe_by_id(rid)
        self.assertIsNotNone(recipe)
        self.assertEqual(recipe["title"], "Test")

    def test_get_ingredients_for_recipe(self):
        recipe_data = {
            "title": "Test",
            "url": "https://example.com/1",
            "clean_ingredients": ["chicken", "onion"],
        }
        rid = database.insert_recipe(recipe_data)
        self.assertIsNotNone(rid)
        ings = database.get_ingredients_for_recipe(rid)
        self.assertEqual(len(ings), 2)
        self.assertIn("chicken", ings)

    def test_new_fields_stored(self):
        """Kiểm tra các trường mới (description, image_url) được lưu."""
        recipe_data = {
            "title": "Test",
            "url": "https://example.com/1",
            "description": "A test recipe",
            "image_url": "https://example.com/img.jpg",
            "clean_ingredients": [],
        }
        rid = database.insert_recipe(recipe_data)
        self.assertIsNotNone(rid)
        recipe = database.get_recipe_by_id(rid)
        self.assertIsNotNone(recipe)
        self.assertEqual(recipe["description"], "A test recipe")
        self.assertEqual(recipe["image_url"], "https://example.com/img.jpg")


# ============================================================================
# 4. TEST CRAWL - Session reuse
# ============================================================================
class TestCrawlSession(unittest.TestCase):
    """Kiểm tra Session tái sử dụng."""

    def test_session_reuse(self):
        """Session được tái sử dụng (lazy init)."""
        import crawler
        crawler._session = None
        s1 = crawler._get_session()
        s2 = crawler._get_session()
        self.assertIs(s1, s2)

    def test_user_agent_not_truncated(self):
        """User-Agent phải đầy đủ."""
        import crawler
        ua = crawler.DEFAULT_HEADERS["User-Agent"]
        self.assertIn("Chrome/", ua)
        self.assertIn("Safari/537.36", ua)


# ============================================================================
# 5. TEST EDGE CASES
# ============================================================================
class TestEdgeCases(unittest.TestCase):
    """Kiểm tra các trường hợp biên."""

    def test_special_characters_in_url(self):
        """URL có ký tự đặc biệt."""
        db_fd, db_path = _make_temp_db()
        original = database.DB_PATH
        _use_db(db_path)
        database.create_tables()

        result = database.insert_recipe({
            "title": "Special",
            "url": "https://www.bbcgoodfood.com/recipes/cr%C3%A8me-br%C3%BBl%C3%A9e",
            "clean_ingredients": ["egg", "sugar"],
        })
        self.assertIsNotNone(result)

        _restore_db(original)
        os.close(db_fd)
        os.unlink(db_path)


# ============================================================================
# 6. TEST ML - RecipeSearchEngine
# ============================================================================
class TestMLSearch(unittest.TestCase):
    """Kiểm tra logic tìm kiếm TF-IDF."""

    def setUp(self):
        self.db_fd, self.db_path = _make_temp_db()
        self.original_db_path = database.DB_PATH
        _use_db(self.db_path)
        database.create_tables()
        
        # Thêm dữ liệu mẫu
        database.insert_recipe({
            "title": "Chicken Curry",
            "url": "https://example.com/1",
            "clean_ingredients": ["chicken", "curry powder", "onion"],
        })
        database.insert_recipe({
            "title": "Tomato Pasta",
            "url": "https://example.com/2",
            "clean_ingredients": ["pasta", "tomato", "garlic", "basil"],
        })

    def tearDown(self):
        _restore_db(self.original_db_path)
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_search_engine_build_and_search(self):
        """Build index và tìm kiếm cơ bản."""
        from ml_search import RecipeSearchEngine
        engine = RecipeSearchEngine()
        engine.build_index()
        
        self.assertTrue(engine.is_fitted)
        self.assertEqual(len(engine.recipes_df), 2)
        
        # Tìm chicken -> Chicken Curry phải đứng đầu
        results = engine.search_by_ingredients("chicken")
        self.assertFalse(results.empty)
        self.assertEqual(results.iloc[0]["title"], "Chicken Curry")
        
    def test_search_no_match(self):
        """Tìm kiếm không có kết quả."""
        from ml_search import RecipeSearchEngine
        engine = RecipeSearchEngine()
        engine.build_index()
        
        results = engine.search_by_ingredients("chocolate")
        self.assertTrue(results.empty)


# ============================================================================
# CHẠY TESTS
# ============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("  BBC GOOD FOOD CRAWLER - TEST SUITE")
    print("=" * 70)
    print()
    unittest.main(verbosity=2)