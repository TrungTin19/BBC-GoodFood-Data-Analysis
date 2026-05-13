# -*- coding: utf-8 -*-
"""
visualize.py - Module thống kê và trực quan hóa dữ liệu
==========================================================
Tạo các biểu đồ: phân bố độ khó, phân bố rating,
top 10 nguyên liệu phổ biến, và các thống kê tổng hợp.
"""

import os
import logging
import sys
import io

# Đảm bảo console Windows hiển thị UTF-8 đúng
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except (AttributeError, io.UnsupportedOperation):
        pass
if sys.stderr.encoding != "utf-8":
    try:
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except (AttributeError, io.UnsupportedOperation):
        pass

import matplotlib
matplotlib.use("Agg")  # Backend không cần GUI
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

from config import CHARTS_DIR
from database import (
    get_all_recipes, get_top_ingredients,
    get_difficulty_distribution, get_statistics
)

logger = logging.getLogger(__name__)

# Cấu hình style
sns.set_theme(style="whitegrid", font_scale=1.1)
plt.rcParams["figure.figsize"] = (10, 6)
plt.rcParams["figure.dpi"] = 150


def plot_difficulty_distribution():
    """Vẽ biểu đồ phân bố độ khó (bar chart)."""
    data = get_difficulty_distribution()
    if not data:
        logger.warning("Không có dữ liệu độ khó.")
        return None

    try:
        labels, counts = zip(*data)
    except ValueError:
        logger.warning("Dữ liệu độ khó không hợp lệ để vẽ biểu đồ.")
        return None

    colors = sns.color_palette("viridis", len(labels))

    fig, ax = plt.subplots()
    bars = ax.bar(labels, counts, color=colors, edgecolor="white", linewidth=0.8)

    # Thêm số liệu trên mỗi cột
    for bar, count in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5,
                str(count), ha="center", va="bottom", fontweight="bold")

    ax.set_xlabel("Difficulty Level")
    ax.set_ylabel("Number of Recipes")
    ax.set_title("Distribution of Recipe Difficulty Levels", fontweight="bold")
    plt.tight_layout()

    path = os.path.join(CHARTS_DIR, "difficulty_distribution.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"Đã lưu biểu đồ: {path}")
    return path


def plot_rating_distribution():
    """Vẽ biểu đồ phân bố rating (histogram)."""
    recipes = get_all_recipes()
    if not recipes:
        return None

    df = pd.DataFrame(recipes)
    ratings = df["rating"].dropna()

    if ratings.empty:
        logger.warning("Không có dữ liệu rating.")
        return None

    fig, ax = plt.subplots()
    sns.histplot(ratings, bins=20, kde=True, color="steelblue", ax=ax,
                 edgecolor="white", linewidth=0.5)

    ax.axvline(ratings.mean(), color="red", linestyle="--", linewidth=1.5,
               label=f"Mean: {ratings.mean():.2f}")
    ax.legend()
    ax.set_xlabel("Rating (0-5)")
    ax.set_ylabel("Number of Recipes")
    ax.set_title("Distribution of Recipe Ratings", fontweight="bold")
    plt.tight_layout()

    path = os.path.join(CHARTS_DIR, "rating_distribution.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"Đã lưu biểu đồ: {path}")
    return path


def plot_top_ingredients(top_n: int = 10):
    """Vẽ biểu đồ top N nguyên liệu phổ biến (horizontal bar)."""
    data = get_top_ingredients(top_n)
    if not data:
        return None

    try:
        ingredients, counts = zip(*data)
    except ValueError:
        logger.warning("Dữ liệu nguyên liệu không hợp lệ để vẽ biểu đồ.")
        return None

    colors = sns.color_palette("magma_r", len(ingredients))

    fig, ax = plt.subplots()
    y_pos = range(len(ingredients))
    bars = ax.barh(y_pos, counts, color=colors, edgecolor="white", linewidth=0.5)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(ingredients)
    ax.invert_yaxis()  # Nguyên liệu phổ biến nhất ở trên

    # Thêm số liệu
    for bar, count in zip(bars, counts):
        ax.text(bar.get_width() + 3, bar.get_y() + bar.get_height() / 2,
                str(count), va="center", fontweight="bold", fontsize=9)

    ax.set_xlabel("Number of Recipes")
    ax.set_title(f"Top {top_n} Most Common Ingredients", fontweight="bold")
    plt.tight_layout()

    path = os.path.join(CHARTS_DIR, "top_ingredients.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"Đã lưu biểu đồ: {path}")
    return path


def plot_prep_cook_time():
    """Vẽ biểu đồ phân bố thời gian chuẩn bị và nấu."""
    recipes = get_all_recipes()
    if not recipes:
        return None

    df = pd.DataFrame(recipes)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Prep time
    prep = df["prep_time_min"].dropna()
    prep = prep[prep <= 180]  # Giới hạn 3 giờ
    if not prep.empty:
        sns.histplot(prep, bins=30, kde=True, color="coral", ax=axes[0],
                     edgecolor="white")
        axes[0].set_xlabel("Prep Time (minutes)")
        axes[0].set_ylabel("Count")
        axes[0].set_title("Prep Time Distribution", fontweight="bold")

    # Cook time
    cook = df["cook_time_min"].dropna()
    cook = cook[cook <= 180]
    if not cook.empty:
        sns.histplot(cook, bins=30, kde=True, color="teal", ax=axes[1],
                     edgecolor="white")
        axes[1].set_xlabel("Cook Time (minutes)")
        axes[1].set_ylabel("Count")
        axes[1].set_title("Cook Time Distribution", fontweight="bold")

    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, "time_distribution.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"Đã lưu biểu đồ: {path}")
    return path


def plot_dietary_labels():
    """Vẽ biểu đồ phân bố chế độ ăn."""
    recipes = get_all_recipes()
    if not recipes:
        return None

    df = pd.DataFrame(recipes)
    labels_count = {}
    for labels_str in df["dietary_labels"].dropna():
        for label in str(labels_str).split(","):
            label = label.strip()
            if label:
                labels_count[label] = labels_count.get(label, 0) + 1

    if not labels_count:
        return None

    # Sắp xếp
    sorted_items = sorted(labels_count.items(), key=lambda x: x[1], reverse=True)
    try:
        labels, counts = zip(*sorted_items[:10])
    except ValueError:
        logger.warning("Dữ liệu chế độ ăn không hợp lệ để vẽ biểu đồ.")
        return None
    colors = sns.color_palette("Set2", len(labels))

    fig, ax = plt.subplots()
    bars = ax.bar(labels, counts, color=colors, edgecolor="white")

    for bar, count in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
                str(count), ha="center", va="bottom", fontweight="bold", fontsize=9)

    ax.set_xlabel("Dietary Label")
    ax.set_ylabel("Number of Recipes")
    ax.set_title("Distribution of Dietary Labels", fontweight="bold")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()

    path = os.path.join(CHARTS_DIR, "dietary_labels.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"Đã lưu biểu đồ: {path}")
    return path


def plot_confusion_matrices():
    """Vẽ confusion matrix heatmap cho các ML classifiers."""
    from ml_search import DietaryClassifier
    from config import DIETARY_LABELS

    results = []
    for label in DIETARY_LABELS:
        clf = DietaryClassifier(label_name=label)
        metrics = clf.train_and_evaluate()
        if metrics and "confusion_matrix" in metrics:
            results.append(metrics)

    if not results:
        logger.warning("Không có kết quả ML để vẽ confusion matrix.")
        return None

    fig, axes = plt.subplots(1, len(results), figsize=(5 * len(results), 4))
    if len(results) == 1:
        axes = [axes]

    for ax, metrics in zip(axes, results):
        cm = metrics["confusion_matrix"]
        label = metrics["label"]
        sns.heatmap(
            cm, annot=True, fmt="d", cmap="Blues", ax=ax,
            xticklabels=[f"Non-{label}", label],
            yticklabels=[f"Non-{label}", label],
            cbar=False,
        )
        acc = metrics.get("accuracy", 0)
        ax.set_title(f"{label}\nAccuracy: {acc:.1%}", fontweight="bold", fontsize=10)
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")

    plt.suptitle("Naive Bayes Classification — Confusion Matrices", fontweight="bold", y=1.02)
    plt.tight_layout()

    path = os.path.join(CHARTS_DIR, "confusion_matrices.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"Đã lưu biểu đồ: {path}")
    return path


def generate_all_charts():
    """Tạo tất cả biểu đồ và in thống kê tổng hợp."""
    print("=" * 60)
    print("THỐNG KÊ TỔNG HỢP")
    print("=" * 60)

    stats = get_statistics()
    for key, val in stats.items():
        print(f"  {key}: {val}")

    print(f"\n{'='*60}")
    print("TẠO BIỂU ĐỒ")
    print(f"{'='*60}")

    charts = [
        ("Phân bố độ khó", plot_difficulty_distribution),
        ("Phân bố rating", plot_rating_distribution),
        ("Top 10 nguyên liệu", plot_top_ingredients),
        ("Thời gian nấu", plot_prep_cook_time),
        ("Chế độ ăn", plot_dietary_labels),
        ("Confusion Matrix (ML)", plot_confusion_matrices),
    ]

    for name, func in charts:
        try:
            path = func()
            status = "✓" if path else "✗ (không đủ dữ liệu)"
        except Exception as e:
            status = f"✗ (lỗi: {e})"
            logger.error(f"Lỗi vẽ biểu đồ '{name}': {e}")
        print(f"  {name}: {status}")

    print(f"\nBiểu đồ được lưu tại: {CHARTS_DIR}")


if __name__ == "__main__":
    generate_all_charts()
