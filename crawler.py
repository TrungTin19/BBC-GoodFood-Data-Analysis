# -*- coding: utf-8 -*-
"""
crawler.py - Module thu thập dữ liệu từ BBC Good Food
=======================================================
Chức năng: Gửi HTTP request an toàn, thu thập URL công thức
qua sitemap XML và các trang collection. Tuân thủ robots.txt.

Chiến lược thu thập:
  1. Đọc sitemap.xml → tìm các quarterly recipe sitemaps
  2. Parse từng recipe sitemap → lấy URL công thức
  3. Bổ sung: crawl các collection pages → lấy thêm URL
"""

import time
import logging
import re
from typing import List, Optional, Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config import (
    BASE_URL, RECIPES_LIST_URL, REQUEST_DELAY, REQUEST_TIMEOUT,
    MAX_RETRIES, RETRY_DELAY, DEFAULT_HEADERS, MIN_RECIPES,
)

# Logging: chỉ tạo logger, KHÔNG gọi basicConfig()
# (main.py đã cấu hình basicConfig rồi, gọi lại sẽ tạo handler trùng)
logger = logging.getLogger(__name__)


# ============================================================
# SESSION TÁI SỬ DỤNG KẾT NỐI HTTP (cải tiến từ dự án bbc_goodfood_crawler)
# ============================================================
_session: Optional[requests.Session] = None


def _get_session() -> requests.Session:
    """
    Khởi tạo hoặc trả về Session đã có (lazy-init).
    Tái sử dụng TCP connection giữa các request → nhanh hơn.
    """
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update(DEFAULT_HEADERS)
    return _session


# ============================================================
# HÀM GỬI REQUEST AN TOÀN
# ============================================================
def safe_request(url: str, max_retries: int = MAX_RETRIES,
                 delay: float = REQUEST_DELAY, timeout: int = REQUEST_TIMEOUT
                 ) -> Optional[requests.Response]:
    """
    Gửi GET request an toàn với cơ chế retry, delay và Session tái sử dụng.
    Tuân thủ Crawl-delay bằng time.sleep sau mỗi request thành công.

    Cải tiến: dùng requests.Session() để tái sử dụng kết nối TCP.
    """
    session = _get_session()
    for attempt in range(1, max_retries + 1):
        try:
            logger.debug(f"Request [{attempt}/{max_retries}]: {url}")
            response = session.get(url, timeout=timeout)

            # HTTP 429 Too Many Requests → exponential backoff
            if response.status_code == 429:
                wait = min(RETRY_DELAY * attempt * 2, 60)
                logger.warning(f"HTTP 429 – chờ {wait}s trước khi thử lại ({attempt}/{max_retries})")
                time.sleep(wait)
                continue

            response.raise_for_status()
            time.sleep(delay)  # Tuân thủ Crawl-delay
            return response
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else 'N/A'
            logger.warning(f"HTTP Error {status} tại {url}")
            if e.response is not None and e.response.status_code == 404:
                return None
            time.sleep(RETRY_DELAY * attempt)
        except requests.exceptions.ConnectionError:
            logger.warning(f"Lỗi kết nối tại {url}. Retry sau {RETRY_DELAY * attempt}s")
            time.sleep(RETRY_DELAY * attempt)
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout tại {url}. Retry sau {RETRY_DELAY * attempt}s")
            time.sleep(RETRY_DELAY * attempt)
        except requests.exceptions.RequestException as e:
            logger.error(f"Lỗi không xác định tại {url}: {e}")
            time.sleep(RETRY_DELAY * attempt)
    logger.error(f"Thất bại sau {max_retries} lần thử: {url}")
    return None


# ============================================================
# THU THẬP URL TỪ SITEMAP XML
# ============================================================
def get_recipe_sitemap_urls() -> List[str]:
    """
    Lấy danh sách URL các recipe sitemap từ sitemap index.

    BBC Good Food tổ chức sitemap theo quý:
      https://www.bbcgoodfood.com/sitemaps/YYYY-QN-recipe.xml

    Returns:
        Danh sách URL sitemap chứa công thức
    """
    sitemap_url = f"{BASE_URL}/sitemap.xml"
    logger.info(f"Đang đọc sitemap index: {sitemap_url}")

    response = safe_request(sitemap_url)
    if response is None:
        logger.error("Không thể đọc sitemap.xml!")
        return []

    soup = BeautifulSoup(response.text, "xml")
    all_locs = soup.find_all("loc")

    # Lọc chỉ lấy recipe sitemaps
    recipe_sitemaps = [
        loc.text.strip() for loc in all_locs
        if "recipe" in loc.text.lower() and loc.text.strip().endswith(".xml")
    ]

    logger.info(f"Tìm thấy {len(recipe_sitemaps)} recipe sitemaps")
    return recipe_sitemaps


def get_urls_from_sitemap(sitemap_url: str) -> List[str]:
    """
    Parse một sitemap XML và lấy tất cả URL công thức.

    Lọc bỏ các URL /premium/ (cần đăng nhập trả phí).

    Args:
        sitemap_url: URL của file sitemap XML

    Returns:
        Danh sách URL công thức
    """
    response = safe_request(sitemap_url)
    if response is None:
        return []

    soup = BeautifulSoup(response.text, "xml")
    urls = []

    for loc in soup.find_all("loc"):
        url = loc.text.strip()
        # Chỉ lấy URL dạng /recipes/ten-mon (không có thêm path con)
        # Bỏ: /premium/, /recipes/collection/, /recipes/category/,
        #      /recipes/vegetarian/..., URL có trailing slash
        if "/recipes/" in url and "/premium/" not in url:
            path = urlparse(url).path
            # Chỉ match dạng /recipes/slug (1 level sau /recipes/)
            if re.match(r"^/recipes/[a-z0-9][a-z0-9\-]*[a-z0-9]$", path):
                urls.append(url)

    return urls


def get_recipe_urls_from_sitemaps(existing_urls: Optional[Set[str]] = None) -> List[str]:
    """
    Thu thập URL công thức từ tất cả recipe sitemaps.

    Args:
        existing_urls: Tập URL đã crawl (để bỏ qua)

    Returns:
        Danh sách URL công thức mới
    """
    if existing_urls is None:
        existing_urls = set()

    sitemap_urls = get_recipe_sitemap_urls()
    if not sitemap_urls:
        return []

    all_urls = set()

    for i, sitemap_url in enumerate(sitemap_urls, 1):
        try:
            urls = get_urls_from_sitemap(sitemap_url)
            new_urls = [u for u in urls if u not in existing_urls and u not in all_urls]
            all_urls.update(new_urls)

            logger.info(
                f"Sitemap [{i}/{len(sitemap_urls)}]: +{len(new_urls)} mới. "
                f"Tổng: {len(all_urls)}"
            )

            # Dừng sớm nếu đã đủ
            if MIN_RECIPES > 0 and len(all_urls) >= MIN_RECIPES:
                logger.info(f"Đã đủ {len(all_urls)} URL (>= {MIN_RECIPES}). Dừng.")
                break

        except Exception as e:
            logger.error(f"Lỗi xử lý sitemap {sitemap_url}: {e}")
            continue

    result = list(all_urls)
    logger.info(f"Sitemap: tổng cộng {len(result)} URL mới")
    return result


# ============================================================
# THU THẬP URL TỪ COLLECTION PAGES (BỔ SUNG)
# ============================================================
def get_collection_urls() -> List[str]:
    """
    Lấy danh sách URL các trang collection từ trang chính /recipes/.

    Returns:
        Danh sách URL collection
    """
    logger.info("Đang tìm các trang collection...")
    response = safe_request(RECIPES_LIST_URL)
    if response is None:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    collections = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/recipes/collection/" in href:
            full_url = href if href.startswith("http") else urljoin(BASE_URL, href)
            collections.add(full_url)

    logger.info(f"Tìm thấy {len(collections)} trang collection")
    return list(collections)


def get_recipe_urls_from_collection(collection_url: str) -> List[str]:
    """
    Thu thập URL công thức từ một trang collection.

    Trang collection BBC Good Food sử dụng full URL cho links,
    nên cần match cả relative path và absolute URL.

    Args:
        collection_url: URL trang collection

    Returns:
        Danh sách URL công thức
    """
    response = safe_request(collection_url)
    if response is None:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    recipe_urls = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]

        # Match absolute URL: https://www.bbcgoodfood.com/recipes/ten-mon
        if re.match(
            r"^https://www\.bbcgoodfood\.com/recipes/[a-z0-9][a-z0-9\-]*[a-z0-9]$",
            href
        ):
            recipe_urls.add(href)
        # Match relative path: /recipes/ten-mon
        elif re.match(r"^/recipes/[a-z0-9][a-z0-9\-]*[a-z0-9]$", href):
            recipe_urls.add(urljoin(BASE_URL, href))

    return list(recipe_urls)


def get_recipe_urls_from_collections(
    existing_urls: Optional[Set[str]] = None,
    max_collections: int = 50,
) -> List[str]:
    """
    Thu thập URL công thức từ các trang collection.

    Args:
        existing_urls: URL đã có
        max_collections: Số collection tối đa crawl

    Returns:
        Danh sách URL công thức mới
    """
    if existing_urls is None:
        existing_urls = set()

    collection_urls = get_collection_urls()
    if not collection_urls:
        return []

    # Giới hạn số collection
    collection_urls = collection_urls[:max_collections]

    all_urls = set()

    for i, coll_url in enumerate(collection_urls, 1):
        try:
            urls = get_recipe_urls_from_collection(coll_url)
            new_urls = [u for u in urls if u not in existing_urls and u not in all_urls]
            all_urls.update(new_urls)

            logger.info(
                f"Collection [{i}/{len(collection_urls)}]: +{len(new_urls)} mới. "
                f"Tổng: {len(all_urls)}"
            )

        except Exception as e:
            logger.error(f"Lỗi collection {coll_url}: {e}")
            continue

    result = list(all_urls)
    logger.info(f"Collections: tổng cộng {len(result)} URL mới")
    return result


# ============================================================
# HÀM CHÍNH: THU THẬP TẤT CẢ URL CÔNG THỨC
# ============================================================
def get_recipe_urls(existing_urls: Optional[Set[str]] = None) -> List[str]:
    """
    Thu thập toàn bộ URL công thức bằng 2 phương pháp:
      1. Sitemap XML (nguồn chính - đầy đủ và nhanh)
      2. Collection pages (nguồn bổ sung)

    Args:
        existing_urls: Tập URL đã crawl trước đó (dùng để resume)

    Returns:
        Danh sách URL công thức mới (chưa crawl)
    """
    if existing_urls is None:
        existing_urls = set()

    logger.info("=" * 50)
    logger.info("PHƯƠNG PHÁP 1: Thu thập từ Sitemap XML")
    logger.info("=" * 50)

    all_urls = set()

    # Phương pháp 1: Sitemap (nhanh, đầy đủ)
    sitemap_urls = get_recipe_urls_from_sitemaps(existing_urls)
    all_urls.update(sitemap_urls)
    logger.info(f"Sau sitemap: {len(all_urls)} URL")

    # Phương pháp 2: Collections (bổ sung nếu chưa đủ)
    if MIN_RECIPES > 0 and len(all_urls) + len(existing_urls) < MIN_RECIPES:
        logger.info("=" * 50)
        logger.info("PHƯƠNG PHÁP 2: Thu thập từ Collection pages")
        logger.info("=" * 50)

        combined_existing = existing_urls | all_urls
        collection_urls = get_recipe_urls_from_collections(combined_existing)
        all_urls.update(collection_urls)
        logger.info(f"Sau collections: {len(all_urls)} URL")

    result = list(all_urls)
    logger.info(f"TỔNG CỘNG: {len(result)} URL công thức mới")
    return result


# ============================================================
# KIỂM TRA robots.txt
# ============================================================
def check_robots_txt() -> dict:
    """Kiểm tra robots.txt để xác nhận quyền crawl /recipes/."""
    response = safe_request(f"{BASE_URL}/robots.txt")
    if response is None:
        return {"allowed": True, "crawl_delay": 1}
    content = response.text
    result = {"raw": content, "allowed": True, "crawl_delay": 1}
    current_agent = None
    for line in content.split("\n"):
        line = line.strip()
        if line.lower().startswith("user-agent:"):
            current_agent = line.split(":", 1)[1].strip()
        elif line.lower().startswith("crawl-delay:") and current_agent == "*":
            try:
                result["crawl_delay"] = int(line.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif line.lower().startswith("disallow:") and current_agent == "*":
            path = line.split(":", 1)[1].strip()
            if path in ("/recipes/", "/recipes"):
                result["allowed"] = False
    return result


# ============================================================
# CÁC HÀM TƯƠNG THÍCH NGƯỢC (cho main.py)
# ============================================================
# Cache danh sách sitemap URLs để tránh fetch lại sitemap.xml mỗi lần gọi
_cached_sitemap_urls: Optional[List[str]] = None


def _get_cached_sitemap_urls() -> List[str]:
    """Lấy danh sách sitemap URLs (cache lần đầu)."""
    global _cached_sitemap_urls
    if _cached_sitemap_urls is None:
        _cached_sitemap_urls = get_recipe_sitemap_urls()
    return _cached_sitemap_urls


def get_total_pages() -> int:
    """Xác định tổng số trang (dùng sitemap thay cho phân trang)."""
    return len(_get_cached_sitemap_urls())


def get_recipe_urls_from_page(page_num: int) -> List[str]:
    """Tương thích ngược: lấy URL từ sitemap thứ page_num."""
    sitemaps = _get_cached_sitemap_urls()
    if 1 <= page_num <= len(sitemaps):
        return get_urls_from_sitemap(sitemaps[page_num - 1])
    return []


# ============================================================
# MAIN - Test module
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("BBC Good Food Crawler - Test")
    print("=" * 60)

    # Kiểm tra robots.txt
    robots = check_robots_txt()
    print(f"robots.txt - Allowed: {robots['allowed']}, Crawl-delay: {robots['crawl_delay']}")

    # Lấy URL từ sitemap
    print("\nTest thu thập URL từ sitemap...")
    urls = get_recipe_urls()
    print(f"Tổng URL: {len(urls)}")
    for u in urls[:5]:
        print(f"  - {u}")
