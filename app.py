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
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Inter:wght@300;400;500;600&display=swap');
    
    :root {
        --primary: #FF4B2B;
        --secondary: #FF416C;
        --accent: #10B981;
    }

    /* Global Styles & Theming */
    .stApp {
        background-color: var(--background-color);
        color: var(--text-color);
    }
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3, .main-header h1 {
        font-family: 'Outfit', sans-serif;
        color: var(--text-color);
    }

    /* Header Section */
    .header-container {
        position: relative;
        height: 320px;
        background: url('https://images.unsplash.com/photo-1504674900247-0877df9cc836?q=80&w=2070&auto=format&fit=crop');
        background-size: cover;
        background-position: center;
        border-radius: 24px;
        margin-bottom: 2rem;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 20px 40px rgba(0,0,0,0.15);
    }

    .header-container::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: linear-gradient(135deg, rgba(31, 41, 55, 0.7) 0%, rgba(255, 75, 43, 0.4) 100%);
        z-index: 1;
    }

    .header-content {
        position: relative;
        z-index: 2;
        text-align: center;
        color: white !important; /* Always white on header */
        padding: 2rem;
    }

    .header-content h1 {
        font-size: 3.5rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        text-shadow: 0 4px 10px rgba(0,0,0,0.3);
        letter-spacing: -1px;
        color: white !important;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: var(--secondary-background-color);
        border-radius: 12px;
        color: var(--text-color);
        font-weight: 600;
        padding: 0 24px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        transition: all 0.3s ease;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, var(--primary) 0%, var(--secondary) 100%) !important;
        color: white !important;
        border: none !important;
    }

    .recipe-card {
        background: var(--secondary-background-color);
        border-radius: 20px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        margin-bottom: 2rem;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        transition: transform 0.3s ease;
    }
    
    .recipe-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        border-color: var(--primary);
    }

    /* Layout Table for alignment */
    .card-layout {
        display: flex;
        flex-direction: row;
        width: 100%;
    }

    @media (max-width: 768px) {
        .card-layout {
            flex-direction: column;
        }
        .card-img-side {
            width: 100% !important;
            height: 200px !important;
        }
    }

    .card-img-side {
        width: 35%;
        min-width: 200px;
        height: 250px;
        overflow: hidden;
        flex-shrink: 0;
    }

    .card-img-side img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    .card-content-side {
        flex-grow: 1;
        padding: 1.5rem;
        display: flex;
        flex-direction: column;
    }

    .recipe-info {
        padding: 1.5rem;
        color: var(--text-color);
    }

    .recipe-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        font-size: 1.4rem;
        color: var(--text-color);
        margin-bottom: 0.75rem;
        line-height: 1.2;
    }

    .recipe-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 1rem;
        font-size: 0.85rem;
        color: var(--text-color);
        opacity: 0.8;
    }

    .meta-item {
        display: flex;
        align-items: center;
        gap: 4px;
        background: rgba(128, 128, 128, 0.1);
        padding: 4px 12px;
        border-radius: 8px;
        color: var(--text-color);
        border: 1px solid rgba(128, 128, 128, 0.1);
    }

    /* Badge styles */
    .diet-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.7rem;
        font-weight: 700;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        color: white;
    }

    /* Sidebar Fix */
    section[data-testid="stSidebar"] {
        background-color: var(--secondary-background-color);
    }
    
    section[data-testid="stSidebar"] .stMarkdown p {
        color: var(--text-color);
    }

    /* Footer */
    .footer {
        text-align: center;
        padding: 3rem 0;
        color: var(--text-color);
        opacity: 0.6;
        border-top: 1px solid rgba(128, 128, 128, 0.2);
        margin-top: 4rem;
    }

    /* Custom Metric styling */
    [data-testid="stMetricValue"] {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        color: var(--primary-color) !important;
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
    # Header with premium background
    st.markdown(f"""
    <div class="header-container animate-fade-in">
        <div class="header-content">
            <h1>🍳 BBC Good Food</h1>
            <p>Smart Recipe Discovery powered by AI & Data Analytics</p>
        </div>
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
                            img_url = row.get('image_url')
                            if not img_url or not isinstance(img_url, str) or not img_url.startswith("http"):
                                img_url = "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?q=80&w=1000&auto=format&fit=crop"
                            
                            # Rating string
                            r_val = row.get('rating')
                            rating_str = f"⭐ {r_val:.1f}" if pd.notna(r_val) else "⭐ N/A"
                            
                            # Difficulty string
                            diff_val = row.get('difficulty')
                            diff = str(diff_val if pd.notna(diff_val) and diff_val else 'Medium').capitalize()
                            
                            # Time info
                            prep = f"⏱️ {int(row['prep_time_min'])}m" if pd.notna(row.get('prep_time_min')) else ""
                            cook = f"🍳 {int(row['cook_time_min'])}m" if pd.notna(row.get('cook_time_min')) else ""
                            
                            # Dietary badges
                            diets = row.get('dietary_labels', '')
                            badges_html = ""
                            if diets:
                                diet_list = [d.strip() for d in diets.split(',') if d.strip()]
                                badges_html = "".join([f'<span class="diet-badge">{d}</span>' for d in diet_list])
                            
                            similarity_html = f'<div style="font-size:0.8rem; color:var(--text-color); opacity:0.6; margin-top:0.5rem;">🎯 Similarity: {row["similarity"]:.4f}</div>' if search_mode != "🔤 Theo tên món ăn" else ""

                            # Header part as pure HTML for perfect layout
                            st.markdown(f"""
                            <div class="recipe-card animate-fade-in">
                                <div class="card-layout">
                                    <div class="card-img-side">
                                        <img src="{img_url}" alt="{row['title']}">
                                    </div>
                                    <div class="card-content-side">
                                        <div class="recipe-title">{row['title']}</div>
                                        <div class="recipe-meta">
                                            <div class="meta-item"><b>{rating_str}</b></div>
                                            <div class="meta-item"><b>{diff}</b></div>
                                            {f'<div class="meta-item">{prep}</div>' if prep else ""}
                                            {f'<div class="meta-item">{cook}</div>' if cook else ""}
                                        </div>
                                        <div style="margin-bottom: 1rem;">{badges_html}</div>
                                        {similarity_html}
                                        <div style="margin-top: auto;">
                                            <a href="{row['url']}" target="_blank" style="text-decoration:none; color:var(--primary); font-weight:600; font-size:0.9rem;">
                                                🔗 View full recipe on BBC Good Food
                                            </a>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                            # Expanders for Ingredients and Instructions
                            with st.container():
                                col_e1, col_e2 = st.columns(2)
                                with col_e1:
                                    raw_ing = row.get("raw_ingredients", "")
                                    if isinstance(raw_ing, str) and raw_ing.strip():
                                        with st.expander("🥕 **Ingredients List**"):
                                            ingredients_list = [ing.strip() for ing in raw_ing.split(";") if ing.strip()]
                                            for ing in ingredients_list:
                                                st.markdown(f"- {ing}")
                                
                                with col_e2:
                                    instructions = row.get("instructions", "")
                                    if isinstance(instructions, str) and instructions.strip():
                                        with st.expander("📖 **Cooking Steps**"):
                                            steps = [s.strip() for s in instructions.split("\n") if s.strip()]
                                            for s in steps:
                                                st.markdown(s)
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

        # Metrics row with custom styling
        st.markdown('<div class="animate-fade-in">', unsafe_allow_html=True)
        
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            st.markdown(f'<div class="metric-container"><div class="metric-value">{stats.get("total_recipes", 0)}</div><div class="metric-label">Total Recipes</div></div>', unsafe_allow_html=True)
        with m_col2:
            st.markdown(f'<div class="metric-container"><div class="metric-value">{stats.get("unique_ingredients", 0)}</div><div class="metric-label">Unique Ingredients</div></div>', unsafe_allow_html=True)
        with m_col3:
            st.markdown(f'<div class="metric-container"><div class="metric-value">{stats.get("avg_rating", 0):.1f}</div><div class="metric-label">Avg Rating</div></div>', unsafe_allow_html=True)
        with m_col4:
            st.markdown(f'<div class="metric-container"><div class="metric-value">{stats.get("avg_cook_time", 0):.0f}m</div><div class="metric-label">Avg Cook Time</div></div>', unsafe_allow_html=True)

        st.markdown('<br>', unsafe_allow_html=True)

        d_col1, d_col2, d_col3 = st.columns(3)
        with d_col1:
            st.markdown(f'<div class="metric-container" style="border-bottom: 4px solid #10B981;"><div class="metric-value" style="color: #10B981;">{stats.get("vegetarian_count", 0)}</div><div class="metric-label">🥬 Vegetarian</div></div>', unsafe_allow_html=True)
        with d_col2:
            st.markdown(f'<div class="metric-container" style="border-bottom: 4px solid #059669;"><div class="metric-value" style="color: #059669;">{stats.get("vegan_count", 0)}</div><div class="metric-label">🌱 Vegan</div></div>', unsafe_allow_html=True)
        with d_col3:
            st.markdown(f'<div class="metric-container" style="border-bottom: 4px solid #3B82F6;"><div class="metric-value" style="color: #3B82F6;">{stats.get("gluten_free_count", 0)}</div><div class="metric-label">🌾 Gluten-free</div></div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

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
    # Footer
    st.markdown("""
    <div class="footer animate-fade-in">
        <p>© 2026 BBC Good Food Analyzer • Created with ❤️ and Streamlit</p>
        <p style="font-size: 0.75rem; opacity: 0.7;">Data Analytics Final Project • Smart Recipe Discovery Engine</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
