# -*- coding: utf-8 -*-
"""
app.py - Giao diện Streamlit cho hệ thống tìm kiếm công thức
===============================================================
Chức năng:
  - Nhập nguyên liệu để tìm kiếm công thức phù hợp
  - Lọc theo rating tối thiểu và chế độ ăn
  - Hiển thị kết quả dạng bảng
  - Hiển thị thống kê và biểu đồ
  - Phân loại chế độ ăn bằng ML
"""

import streamlit as st
import pandas as pd
import os
import sys

# Thêm thư mục gốc vào path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import (
    get_recipe_count, get_statistics, get_top_ingredients,
    get_difficulty_distribution, create_tables
)
from ml_search import RecipeSearchEngine, DietaryClassifier
from config import CHARTS_DIR

# ============================================================
# CẤU HÌNH TRANG
# ============================================================
st.set_page_config(
    page_title="BBC Good Food - Tìm kiếm công thức thông minh",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        border: 1px solid #e9ecef;
    }
    .stDataFrame {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# KHỞI TẠO
# ============================================================
@st.cache_resource
def load_search_engine():
    """Tải và cache search engine."""
    engine = RecipeSearchEngine()
    engine.build_index()
    return engine


@st.cache_resource
def load_classifiers():
    """Tải các classifier đã huấn luyện."""
    classifiers = {}
    for label in ["Vegetarian", "Vegan", "Gluten-free"]:
        clf = DietaryClassifier(label_name=label)
        clf.load_model()
        if clf.is_trained:
            classifiers[label] = clf
    return classifiers


# ============================================================
# GIAO DIỆN CHÍNH
# ============================================================
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🍳 BBC Good Food Recipe Search</h1>
        <p>Tìm kiếm công thức nấu ăn thông minh bằng TF-IDF & Machine Learning</p>
    </div>
    """, unsafe_allow_html=True)

    # Kiểm tra database
    create_tables()
    total_recipes = get_recipe_count()

    if total_recipes == 0:
        st.warning(
            "⚠️ Database trống! Hãy chạy `python main.py` để thu thập dữ liệu trước."
        )
        st.info(
            "Hướng dẫn:\n"
            "1. Mở terminal\n"
            "2. Chạy: `python main.py`\n"
            "3. Đợi quá trình crawl hoàn tất\n"
            "4. Refresh trang này"
        )
        return

    # Sidebar
    st.sidebar.header("🔍 Bộ lọc tìm kiếm")

    # Chọn chế độ tìm kiếm
    search_mode = st.sidebar.radio(
        "Chế độ tìm kiếm:",
        options=["🔤 Theo tên món ăn", "🥕 Theo nguyên liệu"],
        index=0,
    )

    # Input tìm kiếm
    if search_mode == "🔤 Theo tên món ăn":
        query = st.sidebar.text_input(
            "Nhập tên món ăn:",
            placeholder="chicken fajitas",
            help="Ví dụ: pasta, chicken curry, chocolate cake"
        )
    else:
        query = st.sidebar.text_input(
            "Nhập nguyên liệu (cách nhau bằng dấu cách):",
            placeholder="chicken garlic tomato",
            help="Ví dụ: chicken garlic tomato basil"
        )

    # Slider rating
    min_rating = st.sidebar.slider(
        "Rating tối thiểu:",
        min_value=0.0,
        max_value=5.0,
        value=0.0,
        step=0.1,
    )

    # Selectbox chế độ ăn
    dietary_filter = st.sidebar.selectbox(
        "Chế độ ăn:",
        options=["Tất cả", "Vegetarian", "Vegan", "Gluten-free"],
    )

    # Số kết quả
    top_n = st.sidebar.slider("Số kết quả:", 5, 50, 10)

    # Tabs
    tab1, tab2, tab3 = st.tabs(["🔎 Tìm kiếm", "📊 Thống kê", "🤖 ML Classification"])

    # --------------------------------------------------------
    # TAB 1: TÌM KIẾM
    # --------------------------------------------------------
    with tab1:
        if query:
            with st.spinner("Đang tìm kiếm..."):
                engine = load_search_engine()

                if search_mode == "🔤 Theo tên món ăn":
                    # Tìm kiếm theo tên: lọc trực tiếp trên DataFrame
                    if engine.is_fitted and engine.recipes_df is not None:
                        df = engine.recipes_df.copy()
                        # Tìm theo tên (case-insensitive, partial match)
                        mask = df["title"].str.contains(
                            query, case=False, na=False
                        )
                        results = df[mask].copy()
                        results["similarity"] = 1.0  # placeholder

                        # Lọc rating
                        if min_rating > 0:
                            results = results[
                                (results["rating"].notna()) &
                                (results["rating"] >= min_rating)
                            ]

                        # Lọc chế độ ăn
                        if dietary_filter and dietary_filter != "Tất cả":
                            results = results[
                                results["dietary_labels"].str.contains(
                                    dietary_filter, case=False, na=False
                                )
                            ]

                        results = results.head(top_n)[
                            ["title", "url", "rating", "review_count",
                             "difficulty", "dietary_labels", "similarity",
                             "prep_time_min", "cook_time_min",
                             "raw_ingredients", "instructions"]
                        ]
                    else:
                        results = pd.DataFrame()
                else:
                    # Tìm kiếm theo nguyên liệu (TF-IDF)
                    results = engine.search_by_ingredients(
                        query=query,
                        top_n=top_n,
                        min_rating=min_rating,
                        dietary_filter=dietary_filter,
                    )

            if results.empty:
                st.info("Không tìm thấy công thức phù hợp. Thử từ khóa khác!")
            else:
                st.success(f"Tìm thấy {len(results)} công thức phù hợp!")

                # Hiển thị từng kết quả dạng card
                for idx, (_, row) in enumerate(results.iterrows(), 1):
                    with st.container():
                        # Header: Tên món + thông tin nhanh
                        col1, col2, col3 = st.columns([5, 1, 1])
                        with col1:
                            st.markdown(f"### {idx}. {row['title']}")
                        with col2:
                            rating_str = f"⭐ {row['rating']:.1f}" if pd.notna(row.get('rating')) else "N/A"
                            st.markdown(f"**{rating_str}**")
                        with col3:
                            diff = row.get('difficulty', '') or ''
                            st.markdown(f"**{diff}**")

                        # Thông tin thời gian + labels
                        info_parts = []
                        if pd.notna(row.get('prep_time_min')):
                            info_parts.append(f"⏱️ Prep: {int(row['prep_time_min'])} phút")
                        if pd.notna(row.get('cook_time_min')):
                            info_parts.append(f"🍳 Cook: {int(row['cook_time_min'])} phút")
                        if pd.notna(row.get('review_count')) and row['review_count']:
                            info_parts.append(f"📝 {int(row['review_count'])} reviews")
                        if row.get('dietary_labels'):
                            info_parts.append(f"🏷️ {row['dietary_labels']}")
                        if search_mode != "🔤 Theo tên món ăn":
                            info_parts.append(f"🎯 Similarity: {row['similarity']:.4f}")
                        if info_parts:
                            st.caption(" | ".join(info_parts))

                        # Nguyên liệu
                        raw_ing = row.get("raw_ingredients", "")
                        if isinstance(raw_ing, str) and raw_ing.strip():
                            with st.expander("🥕 **Nguyên liệu**", expanded=False):
                                ingredients_list = [
                                    ing.strip() for ing in raw_ing.split(";")
                                    if ing.strip()
                                ]
                                for ing in ingredients_list:
                                    st.markdown(f"- {ing}")

                        # Công thức nấu
                        instructions = row.get("instructions", "")
                        if isinstance(instructions, str) and instructions.strip():
                            with st.expander("📖 **Công thức nấu**", expanded=False):
                                steps = instructions.split("\n")
                                for step in steps:
                                    if step.strip():
                                        st.markdown(f"**{step.strip()}**")
                                        st.write("")  # spacing

                        # Link gốc
                        st.caption(f"🔗 [Xem trên BBC Good Food]({row['url']})")
                        st.divider()
        else:
            st.info(
                "👈 Nhập **tên món ăn** hoặc **nguyên liệu** vào thanh bên trái "
                "để bắt đầu tìm kiếm!\n\n"
                "**Ví dụ:**\n"
                "- Tên món: `chicken fajitas`, `pasta`, `chocolate cake`\n"
                "- Nguyên liệu: `chicken garlic tomato basil`"
            )

    # --------------------------------------------------------
    # TAB 2: THỐNG KÊ
    # --------------------------------------------------------
    with tab2:
        st.subheader("📊 Thống kê tổng hợp")

        stats = get_statistics()

        # Metrics row
        cols = st.columns(4)
        cols[0].metric("Tổng công thức", stats.get("total_recipes", 0))
        cols[1].metric("Nguyên liệu duy nhất", stats.get("unique_ingredients", 0))
        cols[2].metric("Rating trung bình", stats.get("avg_rating", 0))
        cols[3].metric("Thời gian nấu TB", f"{stats.get('avg_cook_time', 0):.0f} phút")

        cols2 = st.columns(3)
        cols2[0].metric("🥬 Vegetarian", stats.get("vegetarian_count", 0))
        cols2[1].metric("🌱 Vegan", stats.get("vegan_count", 0))
        cols2[2].metric("🌾 Gluten-free", stats.get("gluten_free_count", 0))

        # Biểu đồ
        st.subheader("📈 Biểu đồ")

        chart_files = {
            "Phân bố độ khó": "difficulty_distribution.png",
            "Phân bố rating": "rating_distribution.png",
            "Top 10 nguyên liệu": "top_ingredients.png",
            "Thời gian nấu": "time_distribution.png",
            "Chế độ ăn": "dietary_labels.png",
        }

        for title, filename in chart_files.items():
            path = os.path.join(CHARTS_DIR, filename)
            if os.path.exists(path):
                st.image(path, caption=title, width=700)

    # --------------------------------------------------------
    # TAB 3: ML CLASSIFICATION
    # --------------------------------------------------------
    with tab3:
        st.subheader("🤖 Phân loại chế độ ăn bằng Machine Learning")
        st.write("Nhập nguyên liệu để dự đoán chế độ ăn phù hợp:")

        ml_input = st.text_area(
            "Nguyên liệu:",
            placeholder="chicken breast, olive oil, garlic, tomatoes, basil",
            height=100,
        )

        if st.button("🔮 Dự đoán", type="primary"):
            if ml_input:
                classifiers = load_classifiers()
                if not classifiers:
                    st.warning("Chưa có model. Chạy `python main.py` để huấn luyện.")
                else:
                    results = {}
                    for label, clf in classifiers.items():
                        pred, proba = clf.predict(ml_input)
                        results[label] = {"prediction": pred, "confidence": proba}

                    # Hiển thị kết quả
                    cols = st.columns(len(results))
                    for i, (label, res) in enumerate(results.items()):
                        with cols[i]:
                            emoji = "✅" if res["prediction"] == 1 else "❌"
                            st.metric(
                                f"{emoji} {label}",
                                "Có" if res["prediction"] == 1 else "Không",
                                f"Confidence: {res['confidence']:.1%}",
                            )
            else:
                st.warning("Vui lòng nhập nguyên liệu!")


if __name__ == "__main__":
    main()
