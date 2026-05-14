# -*- coding: utf-8 -*-
"""
app.py - Premium Streamlit UI for BBC Good Food Recipe Search
"""

import streamlit as st
import pandas as pd
import os
import sys
from html import escape as html_escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import (
    get_recipe_count, get_statistics, get_top_ingredients,
    get_difficulty_distribution, create_tables
)
from ml_search import RecipeSearchEngine, DietaryClassifier
from config import CHARTS_DIR, DIETARY_LABELS

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="BBC Good Food - Smart Recipe Discovery",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# CSS DESIGN SYSTEM
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&family=Inter:wght@300;400;500;600&display=swap');

    :root {
        --primary: #FF4B2B;
        --secondary: #FF416C;
        --accent: #10B981;
        --accent-dark: #059669;
        --info: #3B82F6;
        --warning: #F59E0B;
    }

    html { scroll-behavior: smooth; }
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    h1, h2, h3 { font-family: 'Outfit', sans-serif; color: var(--text-color); }
    #MainMenu, footer, .stDeployButton { display: none !important; }

    /* ── Hero ── */
    .hero {
        position: relative; height: 260px;
        background: url('https://images.unsplash.com/photo-1504674900247-0877df9cc836?q=80&w=2070&auto=format&fit=crop');
        background-size: cover; background-position: center;
        border-radius: 20px; overflow: hidden;
        display: flex; align-items: center; justify-content: center;
        box-shadow: 0 12px 32px rgba(0,0,0,0.12); margin-bottom: 1.5rem;
    }
    .hero::before {
        content: ""; position: absolute; inset: 0;
        background: linear-gradient(135deg, rgba(15,15,26,0.78) 0%, rgba(255,75,43,0.4) 100%);
    }
    .hero-inner {
        position: relative; z-index: 2; text-align: center; color: white; padding: 1.5rem;
    }
    .hero-inner h1 {
        font-size: 2.8rem; font-weight: 800; color: white !important;
        margin: 0; text-shadow: 0 2px 8px rgba(0,0,0,0.3); letter-spacing: -1px;
    }
    .hero-inner p { margin: 0.25rem 0 0; font-size: 1rem; opacity: 0.85; font-weight: 300; }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; margin-bottom: 1.5rem; }
    .stTabs [data-baseweb="tab"] {
        height: 44px; background: var(--secondary-background-color);
        border-radius: 12px; color: var(--text-color); font-weight: 600;
        padding: 0 24px; border: 1px solid rgba(128,128,128,0.12);
        transition: all 0.3s ease;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%) !important;
        color: white !important; border: none !important;
        box-shadow: 0 6px 15px rgba(255,75,43,0.25);
    }

    /* ── Vertical Card ── */
    .v-card {
        background: var(--secondary-background-color);
        border-radius: 18px; overflow: hidden;
        border: 1px solid rgba(128,128,128,0.1);
        box-shadow: 0 4px 16px rgba(0,0,0,0.04);
        transition: all 0.35s cubic-bezier(0.25,0.46,0.45,0.94);
        margin-bottom: 0.5rem;
    }
    .v-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 16px 40px rgba(0,0,0,0.1);
        border-color: var(--primary);
    }
    .v-card-img { position: relative; width: 100%; height: 200px; overflow: hidden; }
    .v-card-img img {
        width: 100%; height: 100%; object-fit: cover;
        transition: transform 0.5s ease;
    }
    .v-card:hover .v-card-img img { transform: scale(1.05); }

    .v-card-body { padding: 1.1rem 1.3rem 1rem; }
    .v-card-title {
        font-family: 'Outfit', sans-serif; font-weight: 700;
        font-size: 1.1rem; color: var(--text-color);
        margin: 0 0 0.5rem; line-height: 1.3; letter-spacing: -0.3px;
        display: -webkit-box; -webkit-line-clamp: 2;
        -webkit-box-orient: vertical; overflow: hidden;
    }
    .v-card-meta { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 0.6rem; }
    .meta-pill {
        font-size: 0.75rem; padding: 3px 9px; border-radius: 7px;
        background: rgba(128,128,128,0.08); color: var(--text-color);
        font-weight: 500; border: 1px solid rgba(128,128,128,0.06);
    }
    .diet-badge {
        display: inline-block; padding: 3px 10px; border-radius: 9999px;
        font-size: 0.68rem; font-weight: 700; margin-right: 4px;
        background: linear-gradient(135deg, #10B981 0%, #059669 100%); color: white;
    }
    .match-badge {
        position: absolute; top: 10px; left: 10px;
        background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
        color: white; padding: 4px 12px; border-radius: 10px;
        font-size: 0.75rem; font-weight: 700; z-index: 10;
        box-shadow: 0 3px 10px rgba(245,158,11,0.4);
    }
    .v-card-link {
        display: inline-block; margin-top: 0.5rem;
        text-decoration: none; color: var(--primary);
        font-weight: 600; font-size: 0.82rem;
        transition: opacity 0.2s;
    }
    .v-card-link:hover { opacity: 0.7; }

    /* ── Metric Cards ── */
    .metric-card {
        background: var(--secondary-background-color);
        padding: 1.3rem; border-radius: 16px;
        border: 1px solid rgba(128,128,128,0.1);
        text-align: center;
        box-shadow: 0 3px 10px rgba(0,0,0,0.03);
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.07);
        border-color: var(--primary);
    }
    .m-val {
        font-family: 'Outfit', sans-serif; font-size: 2rem; font-weight: 800;
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0.15rem;
    }
    .m-label {
        font-size: 0.8rem; font-weight: 600; color: var(--text-color);
        opacity: 0.65; text-transform: uppercase; letter-spacing: 1px;
    }

    /* ── Empty State ── */
    .empty-state {
        text-align: center; padding: 4rem 2rem;
        color: var(--text-color);
    }
    .empty-state .es-icon { font-size: 4.5rem; margin-bottom: 1rem; opacity: 0.8; }
    .empty-state h3 { margin: 0 0 0.5rem; font-size: 1.4rem; }
    .empty-state p { opacity: 0.55; margin: 0; }

    /* ── Quick Tags ── */
    .quick-tag {
        display: inline-block; padding: 6px 16px; border-radius: 20px;
        background: rgba(128,128,128,0.08); color: var(--text-color);
        font-size: 0.85rem; font-weight: 500; margin: 4px;
        border: 1px solid rgba(128,128,128,0.1);
        transition: all 0.2s;
    }
    .quick-tag:hover { background: var(--primary); color: white; }

    /* ── Section Header ── */
    .section-head {
        font-family: 'Outfit', sans-serif; font-weight: 700;
        font-size: 1.3rem; color: var(--text-color);
        margin-bottom: 1rem; display: flex; align-items: center; gap: 8px;
    }

    /* ── Animations ── */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .animate-in {
        animation: fadeInUp 0.5s ease-out forwards; opacity: 0;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background-image: linear-gradient(180deg, var(--secondary-background-color) 0%, rgba(255,75,43,0.03) 100%);
    }

    /* ── Footer ── */
    .app-footer {
        text-align: center; padding: 2.5rem 0; color: var(--text-color);
        opacity: 0.5; border-top: 1px solid rgba(128,128,128,0.15); margin-top: 3rem;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# CACHE & HELPERS
# ============================================================
@st.cache_resource
def get_cached_search_engine():
    return RecipeSearchEngine()

def load_search_engine():
    engine = get_cached_search_engine()
    if not engine.is_fitted:
        engine.build_index()
    elif engine.is_stale():
        with st.spinner("Đang cập nhật chỉ mục tìm kiếm..."):
            engine.build_index()
    return engine

@st.cache_resource
def load_classifiers(model_type: str = "nb"):
    classifiers = {}
    for label in DIETARY_LABELS:
        clf = DietaryClassifier(label_name=label, model_type=model_type)
        clf.load_model()
        if clf.is_trained:
            classifiers[label] = clf
    return classifiers


def build_card_html(row, search_mode, delay_idx=0):
    """Build vertical card HTML for a single recipe."""
    img_url = row.get('image_url')
    if not img_url or not isinstance(img_url, str) or not img_url.startswith("http"):
        img_url = "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?q=80&w=1000&auto=format&fit=crop"

    safe_title = html_escape(str(row.get('title', '')))
    safe_url = html_escape(str(row.get('url', '')))
    safe_img = html_escape(str(img_url))

    r_val = row.get('rating')
    rating_str = f"⭐ {r_val:.1f}" if pd.notna(r_val) else "⭐ N/A"

    diff_val = row.get('difficulty')
    diff = html_escape(str(diff_val if pd.notna(diff_val) and diff_val else 'Medium').capitalize())

    prep = f"⏱️ {int(row['prep_time_min'])}m" if pd.notna(row.get('prep_time_min')) else ""
    cook = f"🍳 {int(row['cook_time_min'])}m" if pd.notna(row.get('cook_time_min')) else ""

    time_pills = ""
    if prep:
        time_pills += f'<span class="meta-pill">{prep}</span>'
    if cook:
        time_pills += f'<span class="meta-pill">{cook}</span>'

    diets = row.get('dietary_labels', '')
    badges = ""
    if diets:
        for d in [x.strip() for x in diets.split(',') if x.strip()]:
            badges += f'<span class="diet-badge">{html_escape(d)}</span>'

    match_html = ""
    if search_mode != "🔤 Theo tên món ăn" and "match_count" in row.index:
        mc = int(row["match_count"])
        if mc > 0:
            match_html = f'<div class="match-badge">🔍 {mc} matched</div>'

    sim_html = ""
    if search_mode != "🔤 Theo tên món ăn" and "similarity" in row.index:
        sim_html = f'<div style="font-size:0.75rem;opacity:0.5;margin-top:0.3rem">🎯 Score: {row["similarity"]:.4f}</div>'

    delay = delay_idx * 0.07

    return f"""
<div class="v-card animate-in" style="animation-delay:{delay:.2f}s">
<div class="v-card-img">
<img src="{safe_img}" alt="{safe_title}" loading="lazy">
{match_html}
</div>
<div class="v-card-body">
<div class="v-card-title">{safe_title}</div>
<div class="v-card-meta">
<span class="meta-pill"><b>{rating_str}</b></span>
<span class="meta-pill"><b>{diff}</b></span>
{time_pills}
</div>
<div>{badges}</div>
{sim_html}
<a href="{safe_url}" target="_blank" class="v-card-link">🔗 View on BBC Good Food</a>
</div>
</div>"""


def render_card_grid(results, search_mode):
    """Render results as a 2-column grid of vertical cards."""
    items = list(results.iterrows())
    for i in range(0, len(items), 2):
        cols = st.columns(2, gap="medium")
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(items):
                _, row = items[idx]
                with col:
                    html = build_card_html(row, search_mode, delay_idx=idx)
                    html = "\n".join([l for l in html.split('\n') if l.strip()])
                    st.markdown(html, unsafe_allow_html=True)

                    # Expander with details
                    raw_ing = row.get("raw_ingredients", "")
                    instructions = row.get("instructions", "")
                    has_ing = isinstance(raw_ing, str) and raw_ing.strip()
                    has_inst = isinstance(instructions, str) and instructions.strip()

                    if has_ing or has_inst:
                        with st.expander("📋 Chi tiết công thức"):
                            if has_ing:
                                st.markdown("**🥕 Nguyên liệu:**")
                                for ing in [x.strip() for x in raw_ing.split(";") if x.strip()]:
                                    st.markdown(f"- {ing}")
                            if has_inst:
                                st.markdown("**📖 Các bước nấu:**")
                                for s in [x.strip() for x in instructions.split("\n") if x.strip()]:
                                    st.markdown(s)


# ============================================================
# MAIN
# ============================================================
def main():
    # Hero
    st.markdown("""
    <div class="hero animate-in">
        <div class="hero-inner">
            <h1>🍳 BBC Good Food</h1>
            <p>Smart Recipe Discovery powered by AI & Data Analytics</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # DB check
    create_tables()
    total_recipes = get_recipe_count()
    if total_recipes == 0:
        st.warning("⚠️ Database trống! Hãy chạy `python main.py` để thu thập dữ liệu trước.")
        return

    # ── Search Bar (main area) ──
    # Nếu có pending random query, set vào widget key TRƯỚC khi widget render
    if "_pending_random_query" in st.session_state:
        st.session_state["main_query"] = st.session_state.pop("_pending_random_query")

    s_col1, s_col2, s_col3 = st.columns([5, 2, 1])
    with s_col1:
        query = st.text_input(
            "search_main", placeholder="🔍  Tìm kiếm công thức... (VD: chicken, pasta, garlic tomato basil)",
            label_visibility="collapsed", key="main_query",
        )
    with s_col2:
        search_mode = st.selectbox(
            "mode", ["🔤 Theo tên món ăn", "🥕 Theo nguyên liệu"],
            label_visibility="collapsed", key="search_mode_select"
        )
    with s_col3:
        surprise = st.button("🎲 Random", use_container_width=True)

    if surprise:
        engine = load_search_engine()
        if engine.recipes_df is not None and not engine.recipes_df.empty:
            r = engine.recipes_df.sample(1).iloc[0]
            st.session_state["_pending_random_query"] = r["title"]
            st.rerun()

    # ── Sidebar: Advanced Filters ──
    with st.sidebar:
        st.header("⚙️ Bộ lọc nâng cao")
        min_rating = st.slider("Rating tối thiểu:", 0.0, 5.0, 0.0, 0.1)
        dietary_filter = st.selectbox("Chế độ ăn:", ["Tất cả"] + DIETARY_LABELS)
        top_n = st.slider("Số kết quả:", 5, 50, 10)

    # ── Tabs ──
    tab1, tab2, tab3 = st.tabs(["🔎 Tìm kiếm", "📊 Thống kê", "🤖 ML Classification"])

    # ────────────── TAB 1: SEARCH ──────────────
    with tab1:
        if query:
            with st.spinner("Đang tìm kiếm..."):
                engine = load_search_engine()

                if search_mode == "🔤 Theo tên món ăn":
                    if engine.is_fitted and engine.recipes_df is not None:
                        df = engine.recipes_df.copy()
                        mask = df["title"].str.contains(query, case=False, na=False, regex=False)
                        results = df[mask].copy()
                        results["similarity"] = 1.0

                        if min_rating > 0:
                            results = results[
                                (results["rating"].notna()) & (results["rating"] >= min_rating)
                            ]
                        if dietary_filter and dietary_filter != "Tất cả":
                            results = results[
                                results["dietary_labels"].str.contains(dietary_filter, case=False, na=False)
                            ]
                        results = results.head(top_n)
                    else:
                        results = pd.DataFrame()
                else:
                    results = engine.search_by_ingredients(
                        query=query, top_n=top_n,
                        min_rating=min_rating, dietary_filter=dietary_filter,
                    )

                if results is None or results.empty:
                    st.markdown("""
                    <div class="empty-state animate-in">
                        <div class="es-icon">🍽️</div>
                        <h3>Không tìm thấy công thức phù hợp</h3>
                        <p>Thử thay đổi từ khóa hoặc bớt bộ lọc</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown('<div style="text-align:center;margin-top:1rem">', unsafe_allow_html=True)
                    st.caption("💡 Gợi ý: chicken, pasta, chocolate cake, garlic tomato basil")
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.success(f"✨ Tìm thấy **{len(results)}** công thức phù hợp!")
                    render_card_grid(results, search_mode)
        else:
            # ── Trending / Welcome ──
            st.markdown('<div class="section-head animate-in">🔥 Công thức nổi bật</div>', unsafe_allow_html=True)

            engine = load_search_engine()
            if engine.is_fitted and engine.recipes_df is not None:
                trending = engine.recipes_df.dropna(subset=["rating"]).nlargest(6, "rating")
                render_card_grid(trending, "🔤 Theo tên món ăn")
            else:
                st.info("Nhập từ khóa vào ô tìm kiếm phía trên để bắt đầu!")

    # ────────────── TAB 2: STATISTICS ──────────────
    with tab2:
        st.markdown('<div class="section-head">📊 Thống kê tổng hợp</div>', unsafe_allow_html=True)
        stats = get_statistics()

        c1, c2, c3, c4 = st.columns(4)
        for col, val, label in [
            (c1, stats.get("total_recipes", 0), "Total Recipes"),
            (c2, stats.get("unique_ingredients", 0), "Unique Ingredients"),
            (c3, f'{stats.get("avg_rating", 0):.1f}', "Avg Rating"),
            (c4, f'{stats.get("avg_cook_time", 0):.0f}m', "Avg Cook Time"),
        ]:
            with col:
                st.markdown(f'<div class="metric-card animate-in"><div class="m-val">{val}</div><div class="m-label">{label}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        d1, d2, d3 = st.columns(3)
        diet_data = [
            (d1, stats.get("vegetarian_count", 0), "🥬 Vegetarian", "#10B981"),
            (d2, stats.get("vegan_count", 0), "🌱 Vegan", "#059669"),
            (d3, stats.get("gluten_free_count", 0), "🌾 Gluten-free", "#3B82F6"),
        ]
        for col, val, label, color in diet_data:
            with col:
                st.markdown(
                    f'<div class="metric-card animate-in" style="border-bottom:4px solid {color}">'
                    f'<div class="m-val" style="-webkit-text-fill-color:{color}">{val}</div>'
                    f'<div class="m-label">{label}</div></div>',
                    unsafe_allow_html=True
                )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-head">📈 Biểu đồ phân tích</div>', unsafe_allow_html=True)

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
                st.image(path, caption=title, use_container_width=True)

    # ────────────── TAB 3: ML CLASSIFICATION ──────────────
    with tab3:
        st.markdown('<div class="section-head">🤖 Phân loại chế độ ăn bằng Machine Learning</div>', unsafe_allow_html=True)

        col_ml1, col_ml2 = st.columns([3, 1])
        with col_ml1:
            ml_input = st.text_area(
                "Nhập danh sách nguyên liệu để dự đoán:",
                placeholder="chicken breast, olive oil, garlic, tomatoes, basil",
                height=120,
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

                        st.markdown("### 🎯 Kết quả dự đoán:")
                        pred_cols = st.columns(len(results))
                        for i, (label, res) in enumerate(results.items()):
                            with pred_cols[i]:
                                is_pos = res["prediction"] == 1
                                emoji = "✅" if is_pos else "❌"
                                color = "#10b981" if is_pos else "#ef4444"
                                st.markdown(f"""
                                <div class="animate-in" style="padding:1rem;border-radius:14px;border:2px solid {color};background:{color}10;text-align:center;animation-delay:{i*0.1}s">
                                    <div style="font-size:2rem;margin-bottom:0.3rem">{emoji}</div>
                                    <div style="font-weight:700;color:{color};font-size:1rem">{label}</div>
                                    <div style="font-size:0.8rem;color:#6b7280;margin-top:0.2rem">Tin cậy: {res['confidence']:.1%}</div>
                                </div>
                                """, unsafe_allow_html=True)

        # Show confusion matrix chart if available
        cm_path = os.path.join(CHARTS_DIR, "confusion_matrices.png")
        if os.path.exists(cm_path):
            with st.expander("📊 Confusion Matrices (Model Performance)"):
                st.image(cm_path, use_container_width=True)

    # Footer
    st.markdown("""
    <div class="app-footer">
        <p>© 2026 BBC Good Food Analyzer • Created with ❤️ and Streamlit</p>
        <p style="font-size:0.75rem;opacity:0.7">Data Analytics Final Project • Smart Recipe Discovery Engine</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
