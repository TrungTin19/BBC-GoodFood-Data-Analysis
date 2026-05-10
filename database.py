# -*- coding: utf-8 -*-
"""
database.py - Module quản lý cơ sở dữ liệu SQLite
====================================================
Chức năng: Tạo bảng, lưu trữ công thức và nguyên liệu,
truy vấn dữ liệu. Hỗ trợ kiểm tra trùng lặp qua UNIQUE(url).
"""

import sqlite3
import logging
from typing import Dict, List, Optional, Any, Tuple

from config import DB_PATH, DATA_DIR

logger = logging.getLogger(__name__)


def get_connection() -> sqlite3.Connection:
    """Tạo kết nối tới SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")  # Bật ràng buộc khóa ngoại
    conn.execute("PRAGMA journal_mode = WAL")  # Tối ưu hiệu năng ghi
    conn.row_factory = sqlite3.Row  # Trả kết quả dạng dict-like
    return conn


def get_all(query: str = "SELECT * FROM recipes") -> List[Dict]:
    """
    Truy vấn chung theo câu SQL bất kỳ (tương tự Lab4/utils.py).
    Hữu ích khi cần query linh hoạt mà không cần viết hàm riêng.

    ⚠️ Lưu ý: Không truyền dữ liệu người dùng trực tiếp vào tham số query
    để tránh SQL injection. Chỉ dùng với câu SQL hardcoded.

    Args:
        query: Câu SQL SELECT (không chứa user input)

    Returns:
        Danh sách kết quả dạng list[dict]
    """
    conn = get_connection()
    try:
        cursor = conn.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def create_tables():
    """
    Tạo bảng recipes và ingredients nếu chưa tồn tại.
    - recipes: lưu thông tin chính của công thức
    - ingredients: lưu danh sách nguyên liệu sạch (FK → recipes)
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Bảng công thức
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recipes (
                recipe_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                title           TEXT NOT NULL,
                url             TEXT UNIQUE NOT NULL,
                prep_time_min   INTEGER,
                cook_time_min   INTEGER,
                difficulty      TEXT,
                rating          REAL,
                review_count    INTEGER DEFAULT 0,
                dietary_labels  TEXT,
                raw_ingredients TEXT,
                instructions    TEXT,
                description     TEXT,
                image_url       TEXT,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tự động thêm các cột mới nếu chưa tồn tại (tương thích DB cũ)
        for col_name, col_def in [
            ("instructions", "TEXT"),
            ("description", "TEXT"),
            ("image_url", "TEXT"),
            ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ]:
            try:
                cursor.execute(f"ALTER TABLE recipes ADD COLUMN {col_name} {col_def}")
                conn.commit()
                logger.info(f"Đã thêm cột '{col_name}' vào bảng recipes.")
            except sqlite3.OperationalError:
                pass  # Cột đã tồn tại

        # Bảng nguyên liệu (quan hệ N-1 với recipes)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ingredients (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id   INTEGER NOT NULL,
                ingredient  TEXT NOT NULL,
                FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id)
                    ON DELETE CASCADE
            )
        """)

        # Tạo index để tăng tốc truy vấn
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ingredients_recipe
            ON ingredients(recipe_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_recipes_rating
            ON recipes(rating)
        """)

        conn.commit()
        logger.info("Đã tạo/kiểm tra bảng recipes và ingredients.")
    except sqlite3.Error as e:
        logger.error(f"Lỗi tạo bảng: {e}")
        raise
    finally:
        conn.close()


def insert_recipe(recipe_data: Dict[str, Any]) -> Optional[int]:
    """
    Chèn một công thức vào database. Bỏ qua nếu URL đã tồn tại.
    Trả về recipe_id nếu thành công, None nếu trùng lặp.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # INSERT OR IGNORE: bỏ qua nếu url đã tồn tại (UNIQUE constraint)
        cursor.execute("""
            INSERT OR IGNORE INTO recipes
                (title, url, prep_time_min, cook_time_min, difficulty,
                 rating, review_count, dietary_labels, raw_ingredients,
                 instructions, description, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            recipe_data.get("title", "Unknown"),
            recipe_data["url"],
            recipe_data.get("prep_time_min"),
            recipe_data.get("cook_time_min"),
            recipe_data.get("difficulty"),
            recipe_data.get("rating"),
            recipe_data.get("review_count", 0),
            recipe_data.get("dietary_labels", ""),
            recipe_data.get("raw_ingredients", ""),
            recipe_data.get("instructions", ""),
            recipe_data.get("description", ""),
            recipe_data.get("image_url", ""),
        ))

        if cursor.rowcount == 0:
            logger.debug(f"URL đã tồn tại, bỏ qua: {recipe_data['url']}")
            return None

        recipe_id = cursor.lastrowid

        # Chèn nguyên liệu sạch vào bảng ingredients
        clean_ingredients = recipe_data.get("clean_ingredients", [])
        for ing in clean_ingredients:
            if ing.strip():
                cursor.execute(
                    "INSERT INTO ingredients (recipe_id, ingredient) VALUES (?, ?)",
                    (recipe_id, ing.strip())
                )

        conn.commit()
        logger.debug(f"Đã lưu: {recipe_data.get('title', 'N/A')[:40]} (ID={recipe_id})")
        return recipe_id

    except sqlite3.Error as e:
        logger.error(f"Lỗi chèn công thức: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def insert_many_recipes(recipes: List[Dict]) -> int:
    """Chèn nhiều công thức. Trả về số công thức mới được chèn."""
    count = 0
    for r in recipes:
        result = insert_recipe(r)
        if result is not None:
            count += 1
    logger.info(f"Đã chèn {count}/{len(recipes)} công thức mới.")
    return count


def get_existing_urls() -> set:
    """Lấy tập hợp tất cả URL đã có trong database."""
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT url FROM recipes")
        urls = {row["url"] for row in cursor.fetchall()}
        return urls
    finally:
        conn.close()


def get_all_recipes() -> List[Dict]:
    """Lấy toàn bộ công thức từ database."""
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT * FROM recipes ORDER BY recipe_id")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_recipes_paginated(page: int = 1, per_page: int = 20) -> Tuple[List[Dict], int]:
    """
    Lấy công thức có phân trang bằng SQL LIMIT/OFFSET.
    Hiệu quả hơn get_all_recipes() khi database lớn.

    Returns:
        Tuple (danh sách công thức trang hiện tại, tổng số công thức)
    """
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM recipes").fetchone()[0]
        offset = (page - 1) * per_page
        cursor = conn.execute(
            "SELECT * FROM recipes ORDER BY recipe_id LIMIT ? OFFSET ?",
            (per_page, offset)
        )
        recipes = [dict(row) for row in cursor.fetchall()]
        return recipes, total
    finally:
        conn.close()


def get_recipes_with_ingredients() -> List[Dict]:
    """
    Lấy toàn bộ công thức kèm danh sách nguyên liệu sạch.
    Nối nguyên liệu thành chuỗi phân cách bằng dấu cách.
    """
    conn = get_connection()
    try:
        cursor = conn.execute("""
            SELECT r.recipe_id, r.title, r.url, r.rating, r.review_count,
                   r.difficulty, r.dietary_labels, r.prep_time_min, r.cook_time_min,
                   r.raw_ingredients, r.instructions, r.description, r.image_url,
                   GROUP_CONCAT(i.ingredient, ' ') AS ingredients_text
            FROM recipes r
            LEFT JOIN ingredients i ON r.recipe_id = i.recipe_id
            GROUP BY r.recipe_id
            ORDER BY r.recipe_id
        """)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_recipe_by_id(recipe_id: int) -> Optional[Dict]:
    """Lấy công thức theo recipe_id."""
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT * FROM recipes WHERE recipe_id = ?", (recipe_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_ingredients_for_recipe(recipe_id: int) -> List[str]:
    """Lấy danh sách nguyên liệu cho một công thức."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT ingredient FROM ingredients WHERE recipe_id = ? ORDER BY id",
            (recipe_id,),
        )
        return [row["ingredient"] for row in cursor.fetchall()]
    finally:
        conn.close()


def get_recipe_count() -> int:
    """Đếm tổng số công thức trong database."""
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM recipes")
        return cursor.fetchone()["cnt"]
    finally:
        conn.close()


def get_unique_ingredients_count() -> int:
    """Đếm số nguyên liệu duy nhất."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT COUNT(DISTINCT ingredient) as cnt FROM ingredients"
        )
        return cursor.fetchone()["cnt"]
    finally:
        conn.close()


def get_top_ingredients(top_n: int = 10) -> List[Tuple[str, int]]:
    """Lấy top N nguyên liệu phổ biến nhất."""
    conn = get_connection()
    try:
        cursor = conn.execute("""
            SELECT ingredient, COUNT(*) as cnt
            FROM ingredients
            GROUP BY ingredient
            ORDER BY cnt DESC
            LIMIT ?
        """, (top_n,))
        return [(row["ingredient"], row["cnt"]) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_difficulty_distribution() -> List[Tuple[str, int]]:
    """Thống kê phân bố độ khó."""
    conn = get_connection()
    try:
        cursor = conn.execute("""
            SELECT COALESCE(difficulty, 'Unknown') as diff, COUNT(*) as cnt
            FROM recipes
            GROUP BY diff
            ORDER BY cnt DESC
        """)
        return [(row["diff"], row["cnt"]) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_statistics() -> Dict[str, Any]:
    """Lấy các thống kê tổng hợp về dữ liệu."""
    conn = get_connection()
    try:
        stats = {}
        # Tổng số công thức
        stats["total_recipes"] = conn.execute(
            "SELECT COUNT(*) FROM recipes"
        ).fetchone()[0]

        # Tổng số nguyên liệu duy nhất
        stats["unique_ingredients"] = conn.execute(
            "SELECT COUNT(DISTINCT ingredient) FROM ingredients"
        ).fetchone()[0]

        # Rating trung bình
        row = conn.execute(
            "SELECT AVG(rating), MIN(rating), MAX(rating) FROM recipes WHERE rating IS NOT NULL"
        ).fetchone()
        stats["avg_rating"] = round(row[0], 2) if row[0] else 0
        stats["min_rating"] = row[1]
        stats["max_rating"] = row[2]

        # Thời gian trung bình
        row = conn.execute(
            "SELECT AVG(prep_time_min), AVG(cook_time_min) FROM recipes"
        ).fetchone()
        stats["avg_prep_time"] = round(row[0], 1) if row[0] else 0
        stats["avg_cook_time"] = round(row[1], 1) if row[1] else 0

        # Số công thức có dietary labels
        stats["vegetarian_count"] = conn.execute(
            "SELECT COUNT(*) FROM recipes WHERE dietary_labels LIKE '%Vegetarian%'"
        ).fetchone()[0]
        stats["vegan_count"] = conn.execute(
            "SELECT COUNT(*) FROM recipes WHERE dietary_labels LIKE '%Vegan%'"
        ).fetchone()[0]
        stats["gluten_free_count"] = conn.execute(
            "SELECT COUNT(*) FROM recipes WHERE dietary_labels LIKE '%Gluten-free%'"
        ).fetchone()[0]

        return stats
    finally:
        conn.close()


if __name__ == "__main__":
    create_tables()
    print("Database đã được khởi tạo tại:", DB_PATH)
    print("Số công thức hiện có:", get_recipe_count())