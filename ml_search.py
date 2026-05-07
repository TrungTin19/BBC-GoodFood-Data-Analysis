# -*- coding: utf-8 -*-
"""
ml_search.py - Module tìm kiếm TF-IDF và phân loại ML
========================================================
Chức năng:
  1. Tìm kiếm công thức bằng TF-IDF + Cosine Similarity
  2. Phân loại chế độ ăn bằng Naive Bayes (Vegetarian, Vegan, Gluten-free)
  3. Đánh giá mô hình (accuracy, precision, recall, confusion matrix)
"""

import logging
import pickle
import os
from typing import List, Dict, Optional, Tuple, Any

# pyrefly: ignore [missing-import]
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, classification_report, confusion_matrix
)
from sklearn.pipeline import Pipeline

from config import TEST_SIZE, RANDOM_STATE, DEFAULT_TOP_N, DATA_DIR, DIETARY_LABELS
from database import get_recipes_with_ingredients, get_all_recipes

logger = logging.getLogger(__name__)

# Đường dẫn lưu model
MODEL_DIR = os.path.join(DATA_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)


# ============================================================
# 1. TÌM KIẾM BẰNG TF-IDF + COSINE SIMILARITY
# ============================================================
class RecipeSearchEngine:
    """
    Hệ thống tìm kiếm công thức dựa trên TF-IDF và Cosine Similarity.

    Quy trình:
      1. Tải toàn bộ công thức kèm nguyên liệu sạch từ database
      2. Xây dựng ma trận TF-IDF từ tập nguyên liệu
      3. Khi tìm kiếm: biến đổi query thành vector, tính cosine similarity
      4. Lọc và sắp xếp kết quả theo độ tương đồng giảm dần
    """

    def __init__(self):
        """Khởi tạo search engine."""
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=5000,
            ngram_range=(1, 2),  # Unigram + Bigram
        )
        self.tfidf_matrix = None
        self.recipes_df = None
        self.is_fitted = False

    def build_index(self):
        """
        Xây dựng chỉ mục TF-IDF từ database.
        Phải gọi trước khi tìm kiếm.
        """
        logger.info("Đang xây dựng chỉ mục TF-IDF...")

        # Lấy dữ liệu từ database
        recipes = get_recipes_with_ingredients()
        if not recipes:
            logger.error("Không có dữ liệu trong database!")
            return

        self.recipes_df = pd.DataFrame(recipes)

        # Thay thế None bằng chuỗi rỗng
        self.recipes_df["ingredients_text"] = (
            self.recipes_df["ingredients_text"].fillna("")
        )

        # Xây dựng ma trận TF-IDF
        corpus = self.recipes_df["ingredients_text"].tolist()
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        self.is_fitted = True

        logger.info(
            f"Chỉ mục TF-IDF: {self.tfidf_matrix.shape[0]} công thức, "
            f"{self.tfidf_matrix.shape[1]} features"
        )

    def search_by_ingredients(
        self,
        query: str,
        top_n: int = DEFAULT_TOP_N,
        min_rating: float = 0.0,
        dietary_filter: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Tìm kiếm công thức dựa trên nguyên liệu nhập vào.

        Args:
            query: Chuỗi nguyên liệu (vd: "chicken garlic tomato")
            top_n: Số kết quả trả về
            min_rating: Rating tối thiểu (0.0 - 5.0)
            dietary_filter: Lọc chế độ ăn (Vegetarian/Vegan/Gluten-free/None)

        Returns:
            DataFrame chứa top_n công thức phù hợp nhất
        """
        if not self.is_fitted:
            logger.error("Chưa xây dựng chỉ mục! Gọi build_index() trước.")
            return pd.DataFrame()

        # Biến đổi query thành vector TF-IDF
        query_vec = self.vectorizer.transform([query.lower()])

        # Tính Cosine Similarity giữa query và tất cả công thức
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        # Thêm cột similarity vào DataFrame
        results_df = self.recipes_df.copy()
        results_df["similarity"] = similarities

        # Lọc theo rating tối thiểu
        if min_rating > 0:
            results_df = results_df[
                (results_df["rating"].notna()) &
                (results_df["rating"] >= min_rating)
            ]

        # Lọc theo chế độ ăn
        if dietary_filter and dietary_filter != "Tất cả":
            results_df = results_df[
                results_df["dietary_labels"].str.contains(
                    dietary_filter, case=False, na=False
                )
            ]

        # Lọc bỏ kết quả có similarity = 0
        results_df = results_df[results_df["similarity"] > 0]

        # Sắp xếp theo similarity giảm dần
        results_df = results_df.sort_values("similarity", ascending=False)

        # Lấy top_n kết quả
        top_results = results_df.head(top_n)[
            ["title", "url", "rating", "review_count", "difficulty",
             "dietary_labels", "similarity", "prep_time_min", "cook_time_min",
             "raw_ingredients", "instructions"]
        ].copy()

        # Làm tròn similarity
        top_results["similarity"] = top_results["similarity"].round(4)

        logger.info(f"Tìm thấy {len(top_results)} kết quả cho query: '{query}'")
        return top_results


# ============================================================
# 2. PHÂN LOẠI CHẾ ĐỘ ĂN BẰNG NAIVE BAYES
# ============================================================
class DietaryClassifier:
    """
    Phân loại chế độ ăn bằng Multinomial Naive Bayes.

    Sử dụng raw_ingredients làm features, dietary_labels làm nhãn.
    Hỗ trợ phân loại: Vegetarian, Vegan, Gluten-free.
    """

    def __init__(self, label_name: str = "Vegetarian"):
        """
        Khởi tạo classifier.
        Args:
            label_name: Tên nhãn cần phân loại (vd: 'Vegetarian')
        """
        self.label_name = label_name
        self.pipeline = Pipeline([
            ("vectorizer", CountVectorizer(
                stop_words="english",
                max_features=5000,
                ngram_range=(1, 2),
            )),
            ("classifier", MultinomialNB()),
        ])
        self.is_trained = False
        self.metrics = {}

    def prepare_data(self) -> Tuple[pd.Series, pd.Series]:
        """
        Chuẩn bị dữ liệu huấn luyện từ database.

        Returns:
            Tuple (X: raw_ingredients text, y: nhãn nhị phân 0/1)
        """
        recipes = get_all_recipes()
        df = pd.DataFrame(recipes)

        # Lọc bỏ công thức không có nguyên liệu
        df = df[df["raw_ingredients"].notna() & (df["raw_ingredients"] != "")]

        # Tạo nhãn nhị phân
        df["label"] = df["dietary_labels"].apply(
            lambda x: 1 if self.label_name.lower() in str(x).lower() else 0
        )

        X = df["raw_ingredients"]
        y = df["label"]

        logger.info(
            f"Dữ liệu cho '{self.label_name}': "
            f"{len(df)} mẫu, {y.sum()} positive, {len(y) - y.sum()} negative"
        )
        return X, y

    def train_and_evaluate(self) -> Dict[str, Any]:
        """
        Huấn luyện mô hình và đánh giá trên tập test.

        Returns:
            Dict chứa các metric đánh giá
        """

        X, y = self.prepare_data()

        if len(X) < 10:
            logger.error("Không đủ dữ liệu để huấn luyện!")
            return {}

        # Chia train/test (80/20)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE,
            stratify=y if y.sum() >= 2 else None
        )

        logger.info(
            f"Train: {len(X_train)} mẫu, Test: {len(X_test)} mẫu"
        )

        # Huấn luyện
        self.pipeline.fit(X_train, y_train)
        self.is_trained = True

        # Dự đoán
        y_pred = self.pipeline.predict(X_test)

        # Tính các metric
        # Dùng labels=[0,1] để đảm bảo confusion_matrix luôn 2x2
        cm = confusion_matrix(y_test, y_pred, labels=[0, 1])

        # classification_report có thể lỗi nếu chỉ có 1 class
        try:
            report = classification_report(
                y_test, y_pred,
                labels=[0, 1],
                target_names=["Non-" + self.label_name, self.label_name],
                zero_division=0
            )
        except ValueError:
            report = f"Chỉ có 1 class trong tập test (không đủ dữ liệu cho {self.label_name})"

        self.metrics = {
            "label": self.label_name,
            "total_samples": len(X),
            "train_size": len(X_train),
            "test_size": len(X_test),
            "positive_count": int(y.sum()),
            "accuracy": round(accuracy_score(y_test, y_pred), 4),
            "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
            "recall": round(recall_score(y_test, y_pred, zero_division=0), 4),
            "f1_score": round(f1_score(y_test, y_pred, zero_division=0), 4),
            "confusion_matrix": cm.tolist(),
            "classification_report": report,
        }

        logger.info(
            f"[{self.label_name}] Accuracy: {self.metrics['accuracy']}, "
            f"Precision: {self.metrics['precision']}, "
            f"Recall: {self.metrics['recall']}"
        )

        return self.metrics

    def predict(self, text: str) -> Tuple[int, float]:
        """
        Dự đoán chế độ ăn cho một công thức.
        Returns: (label, probability)
        """
        if not self.is_trained:
            logger.error("Mô hình chưa được huấn luyện!")
            return 0, 0.0
        pred = self.pipeline.predict([text])[0]
        proba = self.pipeline.predict_proba([text])[0]
        return int(pred), float(max(proba))

    def save_model(self):
        """Lưu model ra file."""
        path = os.path.join(MODEL_DIR, f"nb_{self.label_name.lower()}.pkl")
        with open(path, "wb") as f:
            pickle.dump(self.pipeline, f)
        logger.info(f"Đã lưu model: {path}")

    def load_model(self):
        """Tải model từ file."""
        path = os.path.join(MODEL_DIR, f"nb_{self.label_name.lower()}.pkl")
        if os.path.exists(path):
            with open(path, "rb") as f:
                self.pipeline = pickle.load(f)
            self.is_trained = True
            logger.info(f"Đã tải model: {path}")
        else:
            logger.warning(f"Không tìm thấy model: {path}")


def train_all_classifiers() -> List[Dict]:
    """
    Huấn luyện tất cả các classifier (Vegetarian, Vegan, Gluten-free).
    Returns: Danh sách kết quả đánh giá cho từng classifier.
    """
    labels = DIETARY_LABELS
    all_results = []

    for label in labels:
        print(f"\n{'='*50}")
        print(f"Huấn luyện classifier: {label}")
        print(f"{'='*50}")

        clf = DietaryClassifier(label_name=label)
        metrics = clf.train_and_evaluate()

        if metrics:
            clf.save_model()
            all_results.append(metrics)

            print(f"Accuracy:  {metrics['accuracy']}")
            print(f"Precision: {metrics['precision']}")
            print(f"Recall:    {metrics['recall']}")
            print(f"F1-Score:  {metrics['f1_score']}")
            print(f"\nConfusion Matrix:")
            cm = metrics['confusion_matrix']
            print(f"  TN={cm[0][0]}  FP={cm[0][1]}")
            print(f"  FN={cm[1][0]}  TP={cm[1][1]}")
            print(f"\n{metrics['classification_report']}")

    return all_results


if __name__ == "__main__":
    print("=" * 60)
    print("BBC Good Food - ML Search & Classification")
    print("=" * 60)

    # Test search engine
    print("\n--- Test Search Engine ---")
    engine = RecipeSearchEngine()
    engine.build_index()

    if engine.is_fitted:
        results = engine.search_by_ingredients("chicken garlic tomato", top_n=5)
        print(results.to_string(index=False))

    # Train classifiers
    print("\n--- Training Classifiers ---")
    train_all_classifiers()
