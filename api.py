# -*- coding: utf-8 -*-
"""
api.py - REST API cho hệ thống BBC Good Food Crawler
======================================================
Cung cấp các endpoint Flask để truy xuất dữ liệu công thức,
tìm kiếm theo nguyên liệu, và thống kê.

API Endpoints:
  GET /api/stats              -> Thống kê tổng quan
  GET /api/recipes?page=1     -> Danh sách công thức (phân trang)
  GET /api/recipes/<id>       -> Chi tiết công thức
  GET /api/search?q=chicken   -> Tìm kiếm theo nguyên liệu (TF-IDF)
  GET /api/search-name?q=pasta -> Tìm kiếm theo tên món ăn
"""

import sys
import os
import logging
import threading

from flask import Flask, jsonify, request
from flask_cors import CORS

# Đảm bảo import đúng khi chạy từ thư mục dự án
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import (
    get_all_recipes, get_recipe_by_id, get_ingredients_for_recipe,
    get_recipe_count, get_unique_ingredients_count, get_top_ingredients,
    get_statistics, create_tables, get_recipes_paginated,
    get_ingredients_for_recipes, search_recipes_by_name,
)
from ml_search import RecipeSearchEngine

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=["http://localhost:8501", "http://127.0.0.1:8501"])  # Chỉ cho phép Streamlit

MAX_QUERY_LENGTH = 300
MAX_TOP_N = 50
MAX_PER_PAGE = 100


def _validation_error(parameter: str, message: str, status_code: int = 400):
    """Return a consistent JSON validation error response."""
    return jsonify({
        "error": "invalid_parameter",
        "parameter": parameter,
        "message": message,
    }), status_code


def _parse_int_arg(name: str, default: int, min_value: int, max_value: int):
    """Parse and range-check an integer query parameter."""
    raw = request.args.get(name)
    if raw is None:
        return default, None
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None, f"'{name}' must be an integer."
    if value < min_value or value > max_value:
        return None, f"'{name}' must be between {min_value} and {max_value}."
    return value, None


def _parse_float_arg(name: str, default: float, min_value: float, max_value: float):
    """Parse and range-check a float query parameter."""
    raw = request.args.get(name)
    if raw is None:
        return default, None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None, f"'{name}' must be a number."
    if value < min_value or value > max_value:
        return None, f"'{name}' must be between {min_value} and {max_value}."
    return value, None


def _parse_query_arg(name: str):
    """Validate a user search query before it reaches SQL/ML code."""
    value = request.args.get(name, "")
    value = value.strip()
    if not value:
        return None, f"'{name}' must not be empty."
    if len(value) > MAX_QUERY_LENGTH:
        return None, f"'{name}' must be at most {MAX_QUERY_LENGTH} characters."
    return value, None


# Đảm bảo database sẵn sàng khi có request đầu tiên
@app.before_request
def _ensure_tables():
    """Tạo bảng nếu chưa tồn tại (chạy 1 lần duy nhất)."""
    if not getattr(app, '_tables_created', False):
        create_tables()
        app._tables_created = True


# ---------------------------------------------------------------------------
# Khởi tạo search engine (cache toàn cục)
# ---------------------------------------------------------------------------
_search_engine = None
_engine_lock = threading.Lock()


def _get_search_engine() -> RecipeSearchEngine:
    """Khởi tạo hoặc trả về search engine đã có, tự động rebuild nếu stale (thread-safe)."""
    global _search_engine
    with _engine_lock:
        if _search_engine is None:
            _search_engine = RecipeSearchEngine()
            _search_engine.build_index()
        elif _search_engine.is_stale():
            logger.info("Chỉ mục cũ, đang tự động rebuild...")
            _search_engine.build_index()
        return _search_engine


# ---------------------------------------------------------------------------
# GET /api/stats - Thống kê tổng quan
# ---------------------------------------------------------------------------
@app.route("/api/stats", methods=["GET"])
def api_stats():
    """GET /api/stats - Thống kê tổng quan về database."""
    try:
        stats = get_statistics()
        stats["top_ingredients"] = [
            {"ingredient": ing, "count": cnt}
            for ing, cnt in get_top_ingredients(10)
        ]
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Lỗi stats: {e}")
        return jsonify({"message": "Lỗi hệ thống khi lấy thống kê"}), 500


# ---------------------------------------------------------------------------
# GET /api/recipes?page=1&per_page=20 - Danh sách công thức
# ---------------------------------------------------------------------------
@app.route("/api/recipes", methods=["GET"])
def api_recipes():
    """GET /api/recipes - Danh sách công thức (phân trang SQL)."""
    try:
        page, error = _parse_int_arg("page", 1, 1, 1_000_000)
        if error:
            return _validation_error("page", error)
        per_page, error = _parse_int_arg("per_page", 20, 1, MAX_PER_PAGE)
        if error:
            return _validation_error("per_page", error)

        # Phân trang ở level SQL (LIMIT/OFFSET) thay vì load toàn bộ
        page_recipes, total = get_recipes_paginated(page, per_page)

        # Thêm danh sách nguyên liệu cho mỗi công thức (Batch để tránh N+1)
        recipe_ids = [r["recipe_id"] for r in page_recipes]
        all_ingredients = get_ingredients_for_recipes(recipe_ids)
        for r in page_recipes:
            r["ingredients"] = all_ingredients.get(r["recipe_id"], [])

        return jsonify({
            "recipes": page_recipes,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
        }), 200
    except Exception as e:
        logger.error(f"Lỗi get_recipes: {e}")
        return jsonify({"message": "Lỗi hệ thống khi lấy danh sách công thức"}), 500


# ---------------------------------------------------------------------------
# GET /api/recipes/<id> - Chi tiết công thức
# ---------------------------------------------------------------------------
@app.route("/api/recipes/<int:recipe_id>", methods=["GET"])
def api_recipe_detail(recipe_id):
    """GET /api/recipes/<id> - Chi tiết một công thức."""
    try:
        recipe = get_recipe_by_id(recipe_id)
        if not recipe:
            return jsonify({"message": "Không tìm thấy công thức"}), 404
        recipe["ingredients"] = get_ingredients_for_recipe(recipe_id)
        return jsonify(recipe), 200
    except Exception as e:
        logger.error(f"Lỗi get_recipe: {e}")
        return jsonify({"message": "Lỗi hệ thống khi lấy chi tiết công thức"}), 500


# ---------------------------------------------------------------------------
# GET /api/search?q=chicken+onion&top_n=10 - Tìm kiếm theo nguyên liệu
# ---------------------------------------------------------------------------
@app.route("/api/search", methods=["GET"])
def api_search():
    """GET /api/search - Tìm kiếm công thức theo nguyên liệu (TF-IDF)."""
    try:
        query, error = _parse_query_arg("q")
        if error:
            return _validation_error("q", error)
        top_n, error = _parse_int_arg("top_n", 10, 1, MAX_TOP_N)
        if error:
            return _validation_error("top_n", error)
        min_rating, error = _parse_float_arg("min_rating", 0, 0, 5)
        if error:
            return _validation_error("min_rating", error)
        dietary_filter = request.args.get("dietary", None, type=str)

        engine = _get_search_engine()
        results = engine.search_by_ingredients(
            query=query,
            top_n=top_n,
            min_rating=min_rating,
            dietary_filter=dietary_filter,
        )

        if results.empty:
            return jsonify({"results": [], "total": 0, "query": query}), 200

        result_list = []
        for _, row in results.iterrows():
            result_list.append({
                "title": row.get("title", ""),
                "url": row.get("url", ""),
                "rating": row.get("rating", 0),
                "dietary_labels": row.get("dietary_labels", ""),
                "similarity": round(float(row.get("similarity", 0)), 4),
                "difficulty": row.get("difficulty", ""),
                "prep_time_min": row.get("prep_time_min"),
                "cook_time_min": row.get("cook_time_min"),
                "raw_ingredients": row.get("raw_ingredients", ""),
                "instructions": row.get("instructions", ""),
                "description": row.get("description", ""),
                "image_url": row.get("image_url", ""),
            })

        return jsonify({
            "results": result_list,
            "total": len(result_list),
            "query": query,
        }), 200
    except Exception as e:
        logger.error(f"Lỗi search: {e}")
        return jsonify({"message": "Lỗi hệ thống khi tìm kiếm theo nguyên liệu"}), 500


# ---------------------------------------------------------------------------
# GET /api/search-name?q=pasta - Tìm kiếm theo tên món ăn
# ---------------------------------------------------------------------------
@app.route("/api/search-name", methods=["GET"])
def api_search_name():
    """GET /api/search-name - Tìm kiếm công thức theo tên (partial match)."""
    try:
        query, error = _parse_query_arg("q")
        if error:
            return _validation_error("q", error)
        top_n, error = _parse_int_arg("top_n", 10, 1, MAX_TOP_N)
        if error:
            return _validation_error("top_n", error)

        # Tìm kiếm theo tên (SQL LIKE)
        matched = search_recipes_by_name(query, top_n)

        # Thêm nguyên liệu (Batch)
        recipe_ids = [r["recipe_id"] for r in matched]
        all_ingredients = get_ingredients_for_recipes(recipe_ids)
        for r in matched:
            r["ingredients"] = all_ingredients.get(r["recipe_id"], [])

        return jsonify({
            "results": matched,
            "total": len(matched),
            "query": query,
        }), 200
    except Exception as e:
        logger.error(f"Lỗi search_name: {e}")
        return jsonify({"message": "Lỗi hệ thống khi tìm kiếm theo tên"}), 500


# ---------------------------------------------------------------------------
# Khởi động server
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Tạo bảng nếu chưa có
    create_tables()

    print("=" * 50)
    print("  BBC GOOD FOOD CRAWLER - REST API")
    print("  Server: http://127.0.0.1:5000")
    print("=" * 50)
    print()
    print("  API Endpoints:")
    print("    GET /api/stats              -> Thống kê")
    print("    GET /api/recipes?page=1     -> Danh sách công thức")
    print("    GET /api/recipes/<id>       -> Chi tiết công thức")
    print("    GET /api/search?q=chicken   -> Tìm theo nguyên liệu")
    print("    GET /api/search-name?q=pasta -> Tìm theo tên")
    print()
    print("  Nhấn Ctrl+C để tắt server.")
    print("=" * 50)

    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1", host="127.0.0.1", port=5000)
