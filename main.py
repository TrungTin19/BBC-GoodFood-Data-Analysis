# -*- coding: utf-8 -*-
"""
main.py - Script điều phối chính cho dự án BBC Good Food
==========================================================
Quy trình thực thi:
  1. Khởi tạo database
  2. Kiểm tra robots.txt
  3. Thu thập URL công thức
  4. Parse dữ liệu chi tiết từng công thức
  5. Lưu vào SQLite
  6. Huấn luyện mô hình ML
  7. Tạo biểu đồ thống kê

Sử dụng: python main.py [--skip-crawl] [--skip-ml] [--skip-charts]
"""

import argparse
import logging
import time
import sys
import os
import io

# Đảm bảo console Windows hiển thị UTF-8 đúng
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from config import LOG_FILE, LOG_FORMAT, LOG_LEVEL

# Cấu hình logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def phase_1_init_database():
    """Phase 1: Khởi tạo database."""
    print("\n" + "=" * 60)
    print("PHASE 1: KHỞI TẠO DATABASE")
    print("=" * 60)

    from database import create_tables, get_recipe_count
    create_tables()
    count = get_recipe_count()
    print(f"  Database đã sẵn sàng. Số công thức hiện có: {count}")
    return count


def phase_2_check_robots():
    """Phase 2: Kiểm tra robots.txt."""
    print("\n" + "=" * 60)
    print("PHASE 2: KIỂM TRA robots.txt")
    print("=" * 60)

    from crawler import check_robots_txt
    robots = check_robots_txt()
    print(f"  Allowed: {robots['allowed']}")
    print(f"  Crawl-delay: {robots['crawl_delay']}")

    if not robots["allowed"]:
        print("  ⚠️ CẢNH BÁO: robots.txt không cho phép crawl /recipes/!")
        print("  Dừng chương trình.")
        sys.exit(1)

    return robots


def phase_3_collect_urls(existing_count: int):
    """Phase 3: Thu thập URL công thức."""
    print("\n" + "=" * 60)
    print("PHASE 3: THU THẬP URL CÔNG THỨC")
    print("=" * 60)

    from crawler import get_recipe_urls
    from database import get_existing_urls

    existing = get_existing_urls()
    print(f"  URL đã có trong database: {len(existing)}")

    if len(existing) >= 1000:
        print(f"  Đã đủ >= 1000 URL. Bỏ qua phase thu thập.")
        return []

    urls = get_recipe_urls(existing_urls=existing)
    print(f"  URL mới thu thập: {len(urls)}")
    return urls


def phase_4_5_parse_and_save(urls):
    """Phase 4+5: Parse dữ liệu và lưu theo batch (tránh mất dữ liệu khi bị dừng)."""
    print("\n" + "=" * 60)
    print("PHASE 4+5: PARSE & LƯU DỮ LIỆU CÔNG THỨC")
    print("=" * 60)

    if not urls:
        print("  Không có URL mới để parse.")
        return 0

    from parser import extract_recipe_data
    from database import insert_recipe, get_recipe_count
    from crawler import safe_request

    total = len(urls)
    BATCH_SIZE = 50
    total_inserted = 0
    total_failed = 0
    batch_recipes = []

    print(f"  Bắt đầu parse {total} công thức (lưu mỗi batch {BATCH_SIZE})...")
    start = time.time()

    from database import insert_recipe_batch

    for i, url in enumerate(urls, 1):
        try:
            data = extract_recipe_data(url)
            if data:
                batch_recipes.append(data)
            else:
                total_failed += 1
        except Exception as e:
            logger.error(f"Lỗi parse {url}: {e}")
            total_failed += 1

        # Lưu theo batch hoặc khi kết thúc
        if len(batch_recipes) >= BATCH_SIZE or (i == total and batch_recipes):
            inserted = insert_recipe_batch(batch_recipes)
            total_inserted += inserted
            batch_recipes = []

        # In tiến trình mỗi 20 công thức
        if i % 20 == 0 or i == total:
            elapsed = time.time() - start
            speed = i / elapsed if elapsed > 0 else 0
            eta = (total - i) / speed if speed > 0 else 0
            print(
                f"  [{i}/{total}] {i/total*100:.1f}% | "
                f"Đã lưu: {total_inserted} | Lỗi: {total_failed} | "
                f"ETA: {eta/60:.1f} phút"
            )

    elapsed = time.time() - start
    count_after = get_recipe_count()
    print(f"\n  Hoàn tất: {total_inserted} mới / {total_failed} lỗi ({elapsed:.1f}s)")
    print(f"  Tổng trong DB: {count_after}")
    return total_inserted


def phase_6_train_ml():
    """Phase 6: Huấn luyện mô hình Machine Learning."""
    print("\n" + "=" * 60)
    print("PHASE 6: HUẤN LUYỆN MÔ HÌNH ML")
    print("=" * 60)

    from database import get_recipe_count
    if get_recipe_count() < 10:
        print("  Không đủ dữ liệu để huấn luyện. Cần ít nhất 10 công thức.")
        return

    from ml_search import train_all_classifiers, RecipeSearchEngine

    # Huấn luyện classifiers (cả NB và Logistic)
    for m_type in ["nb", "logistic"]:
        print(f"\n--- {m_type.upper()} Classifiers ---")
        train_all_classifiers(model_type=m_type)

    # Test search engine
    print("\n--- TF-IDF Search Engine ---")
    engine = RecipeSearchEngine()
    engine.build_index()

    if engine.is_fitted:
        print("  Search engine đã sẵn sàng.")
        # Test tìm kiếm
        test_queries = ["chicken garlic", "pasta tomato", "chocolate sugar butter"]
        for q in test_queries:
            res = engine.search_by_ingredients(q, top_n=3)
            print(f"\n  Query: '{q}'")
            if not res.empty:
                for _, row in res.iterrows():
                    print(f"    - {row['title'][:45]} (sim={row['similarity']:.4f}, ★{row['rating']})")
            else:
                print("    Không tìm thấy kết quả.")


def phase_7_visualize():
    """Phase 7: Tạo biểu đồ thống kê."""
    print("\n" + "=" * 60)
    print("PHASE 7: TẠO BIỂU ĐỒ THỐNG KÊ")
    print("=" * 60)

    from visualize import generate_all_charts
    generate_all_charts()


def main():
    """Hàm chính điều phối toàn bộ quy trình."""
    parser = argparse.ArgumentParser(
        description="BBC Good Food Recipe Crawler & Analyzer"
    )
    parser.add_argument(
        "--skip-crawl", action="store_true",
        help="Bỏ qua phase crawl (dùng dữ liệu đã có)"
    )
    parser.add_argument(
        "--skip-ml", action="store_true",
        help="Bỏ qua phase huấn luyện ML"
    )
    parser.add_argument(
        "--skip-charts", action="store_true",
        help="Bỏ qua phase tạo biểu đồ"
    )
    parser.add_argument(
        "--seed", action="store_true",
        help="Chèn dữ liệu mẫu vào database (không cần crawl)"
    )
    parser.add_argument(
        "--server", action="store_true",
        help="Khởi động REST API server (Flask)"
    )
    parser.add_argument(
        "--test", action="store_true",
        help="Chạy test suite"
    )
    args = parser.parse_args()

    print("╔══════════════════════════════════════════════════════════╗")
    print("║  BBC GOOD FOOD - THU THẬP & PHÂN LOẠI CÔNG THỨC       ║")
    print("║  Đồ án: Kỹ thuật lập trình trong Phân tích dữ liệu    ║")
    print("╚══════════════════════════════════════════════════════════╝")

    start_time = time.time()

    # Chế độ seed dữ liệu mẫu (chạy độc lập, không qua pipeline)
    if args.seed:
        from seed_data import seed_database
        seed_database()
        return

    # Chế độ chạy test (chạy độc lập)
    if args.test:
        import unittest
        loader = unittest.TestLoader()
        suite = loader.discover(os.path.dirname(os.path.abspath(__file__)), pattern="test_all.py")
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        sys.exit(0 if result.wasSuccessful() else 1)

    # Chế độ chạy REST API server (chạy độc lập)
    if args.server:
        from seed_data import seed_database
        seed_database()
        from api import app
        print("\n" + "=" * 50)
        print("  BBC GOOD FOOD - REST API SERVER")
        print("  Server: http://127.0.0.1:5000")
        print("=" * 50)
        print("\n  API Endpoints:")
        print("    GET /api/stats              -> Thống kê")
        print("    GET /api/recipes?page=1     -> Danh sách công thức")
        print("    GET /api/recipes/<id>       -> Chi tiết công thức")
        print("    GET /api/search?q=chicken   -> Tìm theo nguyên liệu")
        print("    GET /api/search-name?q=pasta -> Tìm theo tên")
        app.run(debug=True, host="127.0.0.1", port=5000)
        return

    # Pipeline chính
    # Phase 1: Khởi tạo database
    existing_count = phase_1_init_database()

    if not args.skip_crawl:
        # Phase 2: Kiểm tra robots.txt
        phase_2_check_robots()

        # Phase 3: Thu thập URL
        urls = phase_3_collect_urls(existing_count)

        # Phase 4+5: Parse và lưu (theo batch, an toàn khi bị dừng)
        phase_4_5_parse_and_save(urls)
    else:
        print("\n[SKIP] Bỏ qua phase crawl.")

    if not args.skip_ml:
        # Phase 6: ML
        phase_6_train_ml()
    else:
        print("\n[SKIP] Bỏ qua phase ML.")

    if not args.skip_charts:
        # Phase 7: Biểu đồ
        phase_7_visualize()
    else:
        print("\n[SKIP] Bỏ qua phase biểu đồ.")

    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"HOÀN TẤT! Tổng thời gian: {elapsed:.1f}s ({elapsed/60:.1f} phút)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
