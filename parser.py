# -*- coding: utf-8 -*-
"""
parser.py - Module trích xuất và làm sạch dữ liệu công thức
=============================================================
Chức năng: Parse HTML trang chi tiết công thức, trích xuất
tiêu đề, nguyên liệu, thời gian, độ khó, rating, nhãn chế độ ăn.
Làm sạch nguyên liệu: loại bỏ số lượng, đơn vị, hướng dẫn.
"""

import re
import logging
import json
from typing import Dict, List, Optional, Any

from bs4 import BeautifulSoup

from crawler import safe_request

logger = logging.getLogger(__name__)


def debug_selectors(url: str) -> None:
    """
    In ra tất cả class name tìm được trên trang công thức.
    Hữu ích khi cần kiểm tra selector trước khi crawl full.
    Chạy: python parser.py <url>
    """
    response = safe_request(url)
    if response is None:
        logger.error(f"Không thể tải trang: {url}")
        return

    soup = BeautifulSoup(response.text, "html.parser")

    print(f"\n{'='*70}")
    print(f"DEBUG SELECTORS – {url}")
    print(f"{'='*70}")

    # Kiểm tra JSON-LD
    ld_scripts = soup.find_all("script", type="application/ld+json")
    if ld_scripts:
        print(f"\n[Tìm thấy {len(ld_scripts)} script JSON-LD]")
        for i, script in enumerate(ld_scripts):
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    for item in data:
                        print(f"  Script {i}: @type={item.get('@type', 'N/A')}")
                elif isinstance(data, dict):
                    print(f"  Script {i}: @type={data.get('@type', 'N/A')}")
            except (json.JSONDecodeError, TypeError):
                print(f"  Script {i}: (không parse được JSON)")

    # Liệt kê tất cả tag có class
    print(f"\n[Tất cả CSS class]")
    class_map = {}
    for tag in soup.find_all(True):
        classes = tag.get("class", [])
        if classes:
            class_map.setdefault(tag.name, []).append(" ".join(classes))

    for tag_name in sorted(class_map):
        unique_classes = sorted(set(class_map[tag_name]))
        for cls in unique_classes:
            print(f"  <{tag_name} class=\"{cls}\">")

    total = sum(len(set(v)) for v in class_map.values())
    print(f"\n{'='*70}")
    print(f"Tổng: {total} class unique trên {len(class_map)} loại tag")
    print(f"{'='*70}\n")


def parse_time_to_minutes(time_str: str) -> Optional[int]:
    """
    Chuyển đổi chuỗi thời gian sang phút.
    Ví dụ: '1 hr 20 mins' → 80, '30 mins' → 30, '2 hrs' → 120, '0 mins' → 0

    Sửa bug: trả về 0 khi thời gian hợp lệ bằng 0 (ví dụ: "0 minutes").
    Chỉ trả None khi không parse được.
    """
    if not time_str:
        return None
    time_str = time_str.lower().strip()
    total = 0
    found = False
    # Tìm giờ
    hr_match = re.search(r"(\d+)\s*(?:hr|hour)s?", time_str)
    if hr_match:
        total += int(hr_match.group(1)) * 60
        found = True
    # Tìm phút
    min_match = re.search(r"(\d+)\s*(?:min|minute)s?", time_str)
    if min_match:
        total += int(min_match.group(1))
        found = True
    # Nếu chỉ có số thuần (giả sử là phút)
    if not found:
        num_match = re.search(r"(\d+)", time_str)
        if num_match:
            total = int(num_match.group(1))
            found = True
    return total if found else None


def clean_ingredient(raw: str) -> str:
    """
    Làm sạch nguyên liệu: loại bỏ số lượng, đơn vị, hướng dẫn.
    Ví dụ: '200g skinless chicken breasts, sliced' → 'skinless chicken breasts'
    """
    text = raw.strip()
    # Loại bỏ nội dung trong ngoặc đơn
    text = re.sub(r"\([^)]*\)", "", text)
    # Loại bỏ nội dung sau dấu phẩy (hướng dẫn chế biến)
    text = text.split(",")[0]
    # Loại bỏ số lượng và đơn vị ở đầu chuỗi
    units = (
        r"g|kg|ml|l|litre|litres|oz|lb|lbs|cup|cups|tbsp|tsp|"
        r"tablespoon|tablespoons|teaspoon|teaspoons|"
        r"bunch|bunches|handful|handfuls|pinch|pinches|"
        r"slice|slices|piece|pieces|can|cans|tin|tins|"
        r"pack|packs|packet|packets|bag|bags|jar|jars|"
        r"bottle|bottles|clove|cloves|sprig|sprigs|"
        r"knob|stick|sticks|sheet|sheets|block|blocks|"
        r"large|medium|small|x"
    )
    text = re.sub(
        rf"^\s*[\d½¼¾⅓⅔⅛⅜⅝⅞/.\-–]+\s*(?:{units})?\s*",
        "", text, flags=re.IGNORECASE
    )
    # Loại bỏ các ký tự đặc biệt ở đầu
    text = re.sub(r"^[^a-zA-Z]+", "", text)
    # Chuẩn hóa khoảng trắng
    text = re.sub(r"\s+", " ", text).strip()
    return text.lower()


def extract_recipe_data(url: str) -> Optional[Dict[str, Any]]:
    """
    Trích xuất dữ liệu từ trang chi tiết một công thức.

    Trả về dict chứa: title, url, prep_time_min, cook_time_min,
    difficulty, rating, review_count, dietary_labels, raw_ingredients,
    clean_ingredients.
    """
    response = safe_request(url)
    if response is None:
        logger.warning(f"Không thể truy cập công thức: {url}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    recipe = {"url": url}

    # --- Thử lấy dữ liệu từ JSON-LD (schema.org) ---
    # Trang BBC Good Food có nhiều JSON-LD blocks, cần tìm block Recipe
    json_ld_scripts = soup.find_all("script", type="application/ld+json")
    schema_data = None
    for json_ld in json_ld_scripts:
        try:
            data = json.loads(json_ld.string)
            if isinstance(data, list):
                for item in data:
                    if item.get("@type") == "Recipe":
                        schema_data = item
                        break
            elif isinstance(data, dict):
                if data.get("@type") == "Recipe":
                    schema_data = data
                elif "@graph" in data:
                    for item in data["@graph"]:
                        if item.get("@type") == "Recipe":
                            schema_data = item
                            break
            if schema_data:
                break
        except (json.JSONDecodeError, TypeError):
            pass

    # --- 1. Tiêu đề ---
    if schema_data and "name" in schema_data:
        recipe["title"] = schema_data["name"].strip()
    else:
        h1 = soup.find("h1")
        recipe["title"] = h1.get_text(strip=True) if h1 else "Unknown"

    # --- 2. Nguyên liệu thô ---
    raw_ingredients = []
    if schema_data and "recipeIngredient" in schema_data:
        raw_ingredients = schema_data["recipeIngredient"]
    else:
        # Thử nhiều selector cho ingredients
        selectors = [
            "ul.recipe__ingredients li",
            "section.recipe__ingredients li",
            ".ingredients-list li",
            "[class*='ingredient'] li",
        ]
        for sel in selectors:
            items = soup.select(sel)
            if items:
                raw_ingredients = [li.get_text(strip=True) for li in items]
                break

    recipe["raw_ingredients"] = "; ".join(raw_ingredients)
    recipe["clean_ingredients"] = [
        cleaned for cleaned in
        (clean_ingredient(ing) for ing in raw_ingredients)
        if cleaned
    ]

    # --- 3. Thời gian prep/cook ---
    recipe["prep_time_min"] = None
    recipe["cook_time_min"] = None

    if schema_data:
        prep_iso = schema_data.get("prepTime", "")
        cook_iso = schema_data.get("cookTime", "")
        # Chuyển ISO 8601 duration (PT1H20M) sang phút
        if prep_iso:
            recipe["prep_time_min"] = _parse_iso_duration(prep_iso)
        if cook_iso:
            recipe["cook_time_min"] = _parse_iso_duration(cook_iso)

    # Fallback: tìm từ HTML
    if recipe["prep_time_min"] is None:
        prep_el = soup.find(string=re.compile(r"prep", re.I))
        if prep_el:
            parent = prep_el.find_parent()
            if parent:
                time_text = parent.get_text()
                recipe["prep_time_min"] = parse_time_to_minutes(time_text)

    if recipe["cook_time_min"] is None:
        cook_el = soup.find(string=re.compile(r"cook", re.I))
        if cook_el:
            parent = cook_el.find_parent()
            if parent:
                time_text = parent.get_text()
                recipe["cook_time_min"] = parse_time_to_minutes(time_text)

    # --- 4. Độ khó ---
    recipe["difficulty"] = None
    # Tìm difficulty từ HTML: thường nằm trong thẻ <strong> độc lập
    # hoặc trong phần recipe info (không phải title, nav, script)
    difficulty_levels = ["easy", "more effort", "a challenge"]
    for strong_tag in soup.find_all("strong"):
        text = strong_tag.get_text(strip=True).lower()
        if text in difficulty_levels:
            recipe["difficulty"] = strong_tag.get_text(strip=True)
            break

    # Fallback: tìm trong JSON-LD keywords
    if not recipe["difficulty"] and schema_data and "keywords" in schema_data:
        keywords = schema_data["keywords"]
        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.split(",")]
        for kw in keywords:
            if kw.strip().lower() in difficulty_levels:
                recipe["difficulty"] = kw.strip()
                break

    # --- 5. Rating ---
    recipe["rating"] = None
    recipe["review_count"] = 0

    if schema_data and "aggregateRating" in schema_data:
        agg = schema_data["aggregateRating"]
        try:
            recipe["rating"] = float(agg.get("ratingValue", 0))
            recipe["review_count"] = int(agg.get("ratingCount", 0))
        except (ValueError, TypeError):
            pass

    if recipe["rating"] is None:
        # BBC Good Food: div.rating__values chứa text dạng
        # "A star rating of 4.7 out of 5.238 ratings"
        rating_div = soup.select_one(".rating__values, [class*='rating']")
        if rating_div:
            rating_text = rating_div.get_text(strip=True)
            # Tìm rating dạng "X.X out of 5" hoặc số đầu tiên
            match = re.search(r"(\d+\.?\d*)\s*out of\s*5", rating_text)
            if match:
                try:
                    recipe["rating"] = float(match.group(1))
                except ValueError:
                    pass
            # Tìm review count dạng "238 ratings"
            count_match = re.search(r"(\d+)\s*rating", rating_text)
            if count_match:
                recipe["review_count"] = int(count_match.group(1))

    # --- 6. Nhãn chế độ ăn (dietary labels) ---
    dietary_labels = []
    dietary_keywords = ["vegetarian", "vegan", "gluten-free", "dairy-free",
                        "healthy", "low-fat", "low-calorie", "low-sugar"]

    if schema_data and "keywords" in schema_data:
        keywords = schema_data["keywords"]
        if isinstance(keywords, str):
            keywords = [k.strip().lower() for k in keywords.split(",")]
        else:
            keywords = [k.lower() for k in keywords]
        for kw in keywords:
            for diet in dietary_keywords:
                if diet in kw and diet.title() not in dietary_labels:
                    dietary_labels.append(diet.title())

    # Fallback: tìm từ các thẻ masthead tags trên trang
    # BBC Good Food dùng div.post-header--masthead__tags-item
    tag_selectors = [
        ".post-header--masthead__tags-item",
        "[class*='diet']",
        "[class*='tag-item']",
    ]
    for sel in tag_selectors:
        for el in soup.select(sel):
            text = el.get_text(strip=True).lower()
            for diet in dietary_keywords:
                if diet in text and diet.title() not in dietary_labels:
                    dietary_labels.append(diet.title())
            # Thêm các nhãn phổ biến khác từ trang
            other_diets = ["egg-free", "dairy-free", "nut-free", "low-calorie",
                           "low-fat", "low-sugar", "high-fibre", "high-protein"]
            for od in other_diets:
                if od in text and od.title() not in dietary_labels:
                    dietary_labels.append(od.title())

    recipe["dietary_labels"] = ", ".join(dietary_labels)

    # --- 7. Các bước nấu (instructions) ---
    instructions = []
    if schema_data and "recipeInstructions" in schema_data:
        raw_instructions = schema_data["recipeInstructions"]
        if isinstance(raw_instructions, str):
            # Nếu là chuỗi duy nhất, tách theo dấu chấm hoặc xuống dòng
            instructions = [s.strip() for s in re.split(r'\n+', raw_instructions) if s.strip()]
        elif isinstance(raw_instructions, list):
            for item in raw_instructions:
                if isinstance(item, str):
                    instructions.append(item.strip())
                elif isinstance(item, dict):
                    # HowToStep hoặc HowToSection
                    if item.get("@type") == "HowToSection":
                        for sub_item in item.get("itemListElement", []):
                            text = sub_item.get("text", "").strip()
                            if text:
                                instructions.append(text)
                    else:
                        text = item.get("text", "").strip()
                        if text:
                            instructions.append(text)

    # Fallback: tìm từ HTML
    if not instructions:
        method_selectors = [
            ".recipe__method-steps li",
            "section.recipe__method-steps li",
            ".method-steps li",
            ".grouped-list li",
            "[class*='method'] li",
            "[class*='instruction'] li",
            "[class*='steps'] li",
        ]
        for sel in method_selectors:
            items = soup.select(sel)
            if items:
                instructions = [li.get_text(strip=True) for li in items if li.get_text(strip=True)]
                break

    # Đánh số bước nấu
    numbered_steps = []
    for idx, step in enumerate(instructions, 1):
        # Loại bỏ số thứ tự có sẵn ở đầu (nếu có)
        step_clean = re.sub(r'^(?:step\s*)?\d+[\.\)\s:]+\s*', '', step, flags=re.IGNORECASE).strip()
        if step_clean:
            numbered_steps.append(f"Step {idx}: {step_clean}")

    recipe["instructions"] = "\n".join(numbered_steps)

    logger.info(f"Parsed: {recipe['title'][:50]}")
    return recipe


def _parse_iso_duration(iso_str: str) -> Optional[int]:
    """Chuyển ISO 8601 duration (PT1H20M) sang phút."""
    if not iso_str:
        return None
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?", iso_str)
    if not match:
        return None
    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    total = hours * 60 + minutes
    return total if total > 0 else None


def parse_multiple_recipes(urls: List[str],
                           progress_callback=None) -> List[Dict]:
    """
    Parse nhiều công thức từ danh sách URL.
    progress_callback(current, total) được gọi sau mỗi công thức.
    """
    results = []
    total = len(urls)
    for i, url in enumerate(urls, 1):
        try:
            data = extract_recipe_data(url)
            if data and data.get("title") != "Unknown":
                results.append(data)
        except Exception as e:
            logger.error(f"Lỗi parse {url}: {e}")
        if progress_callback:
            progress_callback(i, total)
        if i % 50 == 0:
            logger.info(f"Đã parse {i}/{total} ({len(results)} thành công)")
    logger.info(f"Hoàn tất parse {len(results)}/{total} công thức.")
    return results


if __name__ == "__main__":
    test_url = "https://www.bbcgoodfood.com/recipes/easy-chicken-fajitas"
    print("Test parse công thức:", test_url)
    result = extract_recipe_data(test_url)
    if result:
        for k, v in result.items():
            if k == "clean_ingredients":
                print(f"  {k}: {v[:5]}...")
            else:
                print(f"  {k}: {v}")
