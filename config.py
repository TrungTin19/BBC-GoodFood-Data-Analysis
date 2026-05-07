# -*- coding: utf-8 -*-
"""
config.py - Cấu hình chung cho dự án BBC Good Food Crawler
============================================================
Chứa tất cả các hằng số, đường dẫn, và cài đặt dùng chung
trong toàn bộ dự án.
"""

import os

# ============================================================
# 1. CẤU HÌNH THƯ MỤC VÀ FILE
# ============================================================
# Thư mục gốc của dự án
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Đường dẫn tới file cơ sở dữ liệu SQLite
DB_PATH = os.path.join(BASE_DIR, "data", "recipes.db")

# Thư mục lưu dữ liệu
DATA_DIR = os.path.join(BASE_DIR, "data")

# Thư mục lưu biểu đồ
CHARTS_DIR = os.path.join(BASE_DIR, "charts")

# Thư mục lưu log
LOG_DIR = os.path.join(BASE_DIR, "logs")

# Tạo các thư mục nếu chưa tồn tại
for dir_path in [DATA_DIR, CHARTS_DIR, LOG_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# ============================================================
# 2. CẤU HÌNH CRAWL
# ============================================================
# URL gốc của BBC Good Food
BASE_URL = "https://www.bbcgoodfood.com"

# URL trang danh sách công thức (phân trang)
RECIPES_LIST_URL = "https://www.bbcgoodfood.com/recipes"

# Số trang tối đa cần crawl (0 = tất cả)
MAX_PAGES = 0

# Số công thức tối thiểu cần thu thập
MIN_RECIPES = 1000

# Thời gian chờ giữa các request (giây) - tuân thủ Crawl-delay: 1
REQUEST_DELAY = 1.0

# Thời gian timeout cho mỗi request (giây)
REQUEST_TIMEOUT = 30

# Số lần retry khi request thất bại
MAX_RETRIES = 3

# Thời gian chờ giữa các lần retry (giây)
RETRY_DELAY = 2.0

# User-Agent giả lập trình duyệt
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Headers mặc định cho request
DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

# ============================================================
# 3. CẤU HÌNH MACHINE LEARNING
# ============================================================
# Tỷ lệ chia train/test
TEST_SIZE = 0.2

# Random seed để đảm bảo tái lập kết quả
RANDOM_STATE = 42

# Các nhãn chế độ ăn cần phân loại
DIETARY_LABELS = ["Vegetarian", "Vegan", "Gluten-free"]

# ============================================================
# 4. CẤU HÌNH TÌM KIẾM TF-IDF
# ============================================================
# Số kết quả mặc định khi tìm kiếm
DEFAULT_TOP_N = 10

# Rating tối thiểu mặc định
DEFAULT_MIN_RATING = 0.0

# ============================================================
# 5. CẤU HÌNH LOGGING
# ============================================================
LOG_FILE = os.path.join(LOG_DIR, "crawler.log")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"
