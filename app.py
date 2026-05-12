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
from config import CHARTS_DIR, DIETARY_LABELS

# ============================================================
# CẤU HÌNH TRANG
# ============================================================
st.set_page_config(
    page_title="BBC Good Food - Tìm kiếm công thức thông minh",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for Premium Look
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .main-header {
        text-align: center;
        padding: 2.5rem 0;
        background: linear-gradient(135deg, #1a2a6c 0%, #b21f1f 50%, #fdbb2d 100%);
        color: white;
        border-radius: 15px;
        margin-bottom: 2.5rem;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        font-weight: 700;
        letter-spacing: -0.5px;
        margin-bottom: 0.5rem;
    }
    
    .main-header p {
        font-weight: 300;
        opacity: 0.9;
    }
    
    .recipe-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #eee;
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    
    .recipe-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 20px rgba(0,0,0,0.08);
        border-color: #d1d5db;
    }
    
    .metric-card {
        background: #ffffff;
        padding: 1.2rem;
        border-radius: 12px;
        text-align: center;
        border: 1px solid #f3f4f6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
    
    .diet-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.5rem;
        background: #f3f4f6;
        color: #374151;
    }
    
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s;
    }
    
    .stButton>button:hover {
        transform: scale(1.02);
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
def load_classifiers(model_type: str = "nb"):
    """Tải các classifier đã huấn luyện."""
    classifiers = {}
    for label in DIETARY_LABELS:
        clf = DietaryClassifier(label_name=label, model_type=model_type)
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

    # Nút Surprise Me
    if st.sidebar.button("🎲 Surprise Me! (Món ngẫu nhiên)", use_container_width=True):
        engine = load_search_engine()
        if engine.recipes_df is not None and not engine.recipes_df.empty:
            random_recipe = engine.recipes_df.sample(1).iloc[0]
            st.session_state["search_query"] = random_recipe["title"]
            st.session_state["search_mode"] = "🔤 Theo tên món ăn"
        else:
            st.sidebar.error("Database không có dữ liệu!")

    # Chọn chế độ tìm kiếm
    search_mode = st.sidebar.radio(
        "Chế độ tìm kiếm:",
        options=["🔤 Theo tên món ăn", "🥕 Theo nguyên liệu"],
        index=0,
        key="search_mode"
    )

    # Input tìm kiếm
    query_val = st.session_state.get("search_query", "")
    if search_mode == "🔤 Theo tên món ăn":
        query = st.sidebar.text_input(
            "Nhập tên món ăn:",
            value=query_val,
            placeholder="chicken fajitas",
            help="Ví dụ: pasta, chicken curry, chocolate cake"
        )
    else:
        query = st.sidebar.text_input(
            "Nhập nguyên liệu (cách nhau bằng dấu cách):",
            value=query_val,
            placeholder="chicken garlic tomato",
            help="Ví dụ: chicken garlic tomato basil"
        )
    
    # Cập nhật query vào session state
    if query != query_val:
        st.session_state["search_query"] = query

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
        options=["Tất cả"] + DIETARY_LABELS,
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
                            query, case=False, na=False, regex=False
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
                             "raw_ingredients", "instructions", "image_url"]
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
                        st.markdown('<div class="recipe-card">', unsafe_allow_html=True)
                        
                        col_img, col_content = st.columns([1, 2])
                        
                        with col_img:
                            img_url = row.get('image_url')
                            if img_url and isinstance(img_url, str) and img_url.startswith("http"):
                                st.image(img_url, use_container_width=True)
                            else:
                                st.image("https://via.placeholder.com/300x200?text=No+Image", use_container_width=True)
                        
                        with col_content:
                            # Header: Tên món + thông tin nhanh
                            st.markdown(f"### {idx}. {row['title']}")
                            
                            r_val = row.get('rating')
                            rating_str = f"⭐ {r_val:.1f}" if pd.notna(r_val) else "N/A"
                            diff = row.get('difficulty', '') or 'Medium'
                            
                            st.markdown(f"**{rating_str}** | **{diff}**")

                            # Thông tin thời gian + labels
                            info_parts = []
                            if pd.notna(row.get('prep_time_min')):
                                info_parts.append(f"⏱️ Prep: {int(row['prep_time_min'])}m")
                            if pd.notna(row.get('cook_time_min')):
                                info_parts.append(f"🍳 Cook: {int(row['cook_time_min'])}m")
                            if pd.notna(row.get('review_count')) and row['review_count']:
                                info_parts.append(f"📝 {int(row['review_count'])} reviews")
                            
                            if info_parts:
                                st.write(" | ".join(info_parts))
                                
                            # Dietary labels as badges
                            diets = row.get('dietary_labels', '')
                            if diets:
                                diet_list = [d.strip() for d in diets.split(',') if d.strip()]
                                badges_html = "".join([f'<span class="diet-badge">{d}</span>' for d in diet_list])
                                st.markdown(badges_html, unsafe_allow_html=True)
                            
                            if search_mode != "🔤 Theo tên món ăn":
                                st.caption(f"🎯 Similarity: {row['similarity']:.4f}")

                            # Link gốc
                            st.markdown(f"🔗 [Xem trên BBC Good Food]({row['url']})")

                        # Nguyên liệu & Công thức (Expanders)
                        col_exp1, col_exp2 = st.columns(2)
                        with col_exp1:
                            raw_ing = row.get("raw_ingredients", "")
                            if isinstance(raw_ing, str) and raw_ing.strip():
                                with st.expander("🥕 **Nguyên liệu**"):
                                    ingredients_list = [
                                        ing.strip() for ing in raw_ing.split(";")
                                        if ing.strip()
                                    ]
                                    for ing in ingredients_list:
                                        st.markdown(f"- {ing}")
                        
                        with col_exp2:
                            instructions = row.get("instructions", "")
                            if isinstance(instructions, str) and instructions.strip():
                                with st.expander("📖 **Công thức nấu**"):
                                    steps = instructions.split("\n")
                                    for step in steps:
                                        if step.strip():
                                            st.markdown(f"{step.strip()}")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
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
        
        col_ml1, col_ml2 = st.columns([3, 1])
        with col_ml1:
            ml_input = st.text_area(
                "Nhập danh sách nguyên liệu để dự đoán:",
                placeholder="chicken breast, olive oil, garlic, tomatoes, basil",
                height=150,
            )
        with col_ml2:
            model_type_choice = st.selectbox(
                "Loại mô hình:",
                options=["Naive Bayes (NB)", "Logistic Regression (LR)"],
                index=0
            )
            model_type = "nb" if "NB" in model_type_choice else "logistic"
            st.info(f"Đang sử dụng: **{model_type.upper()}**")

        if st.button("🔮 Dự đoán Chế độ ăn", type="primary", use_container_width=True):
            if ml_input:
                with st.spinner(f"Đang dự đoán bằng {model_type.upper()}..."):
                    classifiers = load_classifiers(model_type=model_type)
                    if not classifiers:
                        st.error(f"Chưa có model {model_type.upper()}. Hãy chạy `python main.py` để huấn luyện.")
                    else:
                        results = {}
                        for label, clf in classifiers.items():
                            pred, proba = clf.predict(ml_input)
                            results[label] = {"prediction": pred, "confidence": proba}

                        # Hiển thị kết quả
                        st.markdown("### 🎯 Kết quả dự đoán:")
                        cols = st.columns(len(results))
                        for i, (label, res) in enumerate(results.items()):
                            with cols[i]:
                                is_pos = res["prediction"] == 1
                                emoji = "✅" if is_pos else "❌"
                                color = "#10b981" if is_pos else "#ef4444"
                                
                                st.markdown(f"""
                                <div style="padding:1rem; border-radius:10px; border:2px solid {color}; background:{color}10; text-align:center;">
                                    <h2 style="margin:0;">{emoji}</h2>
                                    <p style="margin:0; font-weight:600; color:{color};">{label}</p>
                                    <p style="margin:0; font-size:0.8rem; color:#6b7280;">Tin cậy: {res['confidence']:.1%}</p>
                                </div>
                                """, unsafe_allow_html=True)
            else:
                st.warning("Vui lòng nhập nguyên liệu!")


if __name__ == "__main__":
    main()
