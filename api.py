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

from flask import Flask, jsonify, request

# Đảm bảo import đúng khi chạy từ thư mục dự án
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import (
    get_all_recipes, get_recipe_by_id, get_ingredients_for_recipe,
    get_recipe_count, get_unique_ingredients_count, get_top_ingredients,
    get_statistics, create_tables, get_recipes_paginated,
)
from ml_search import RecipeSearchEngine

logger = logging.getLogger(__name__)

# Đảm bảo database sẵn sàng khi module được import (ví dụ: flask run)
create_tables()

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Khởi tạo search engine (cache toàn cục)
# ---------------------------------------------------------------------------
_search_engine = None


def _get_search_engine() -> RecipeSearchEngine:
    """Khởi tạo hoặc trả về search engine đã có."""
    global _search_engine
    if _search_engine is None:
        _search_engine = RecipeSearchEngine()
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
        return jsonify({"message": f"Lỗi: {str(e)}"}), 500


# ---------------------------------------------------------------------------
# GET /api/recipes?page=1&per_page=20 - Danh sách công thức
# ---------------------------------------------------------------------------
@app.route("/api/recipes", methods=["GET"])
def api_recipes():
    """GET /api/recipes - Danh sách công thức (phân trang SQL)."""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)

        # Phân trang ở level SQL (LIMIT/OFFSET) thay vì load toàn bộ
        page_recipes, total = get_recipes_paginated(page, per_page)

        # Thêm danh sách nguyên liệu cho mỗi công thức
        for r in page_recipes:
            r["ingredients"] = get_ingredients_for_recipe(r["recipe_id"])

        return jsonify({
            "recipes": page_recipes,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
        }), 200
    except Exception as e:
        logger.error(f"Lỗi get_recipes: {e}")
        return jsonify({"message": f"Lỗi: {str(e)}"}), 500


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
        return jsonify({"message": f"Lỗi: {str(e)}"}), 500


# ---------------------------------------------------------------------------
# GET /api/search?q=chicken+onion&top_n=10 - Tìm kiếm theo nguyên liệu
# ---------------------------------------------------------------------------
@app.route("/api/search", methods=["GET"])
def api_search():
    """GET /api/search - Tìm kiếm công thức theo nguyên liệu (TF-IDF)."""
    try:
        query = request.args.get("q", "")
        top_n = request.args.get("top_n", 10, type=int)
        min_rating = request.args.get("min_rating", 0, type=float)
        dietary_filter = request.args.get("dietary", None, type=str)

        if not query.strip():
            return jsonify({"message": "Thiếu tham số 'q' (nguyên liệu)"}), 400

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
            })

        return jsonify({
            "results": result_list,
            "total": len(result_list),
            "query": query,
        }), 200
    except Exception as e:
        logger.error(f"Lỗi search: {e}")
        return jsonify({"message": f"Lỗi: {str(e)}"}), 500


# ---------------------------------------------------------------------------
# GET /api/search-name?q=pasta - Tìm kiếm theo tên món ăn
# ---------------------------------------------------------------------------
@app.route("/api/search-name", methods=["GET"])
def api_search_name():
    """GET /api/search-name - Tìm kiếm công thức theo tên (partial match)."""
    try:
        query = request.args.get("q", "")
        top_n = request.args.get("top_n", 10, type=int)

        if not query.strip():
            return jsonify({"message": "Thiếu tham số 'q' (tên món ăn)"}), 400

        all_recipes = get_all_recipes()
        matched = [
            r for r in all_recipes
            if query.lower() in (r.get("title") or "").lower()
        ][:top_n]

        # Thêm nguyên liệu
        for r in matched:
            r["ingredients"] = get_ingredients_for_recipe(r["recipe_id"])

        return jsonify({
            "results": matched,
            "total": len(matched),
            "query": query,
        }), 200
    except Exception as e:
        logger.error(f"Lỗi search_name: {e}")
        return jsonify({"message": f"Lỗi: {str(e)}"}), 500


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

    app.run(debug=True, host="127.0.0.1", port=5000)