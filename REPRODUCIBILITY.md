# REPRODUCIBILITY

Tài liệu này ghi các lệnh tái lập kiểm thử, báo cáo chất lượng dữ liệu, EDA và đánh giá mô hình trên Windows PowerShell. Trọng tâm là chạy offline từ SQLite database hiện có, phù hợp cho chấm bài môn Lập trình trong phân tích dữ liệu.

## 1. Chuẩn bị môi trường

```powershell
cd "C:\Users\dhp01\OneDrive\Máy tính\bai-tap\BBC-GoodFood-Data-Analysis"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 2. Chạy test

```powershell
python -m pytest -q
python test_all.py
```

Kết quả xác nhận gần nhất:

- `python -m pytest -q`: PASS, `48 passed`
- `python test_all.py`: PASS, `Ran 31 tests`, `OK`

## 3. Chạy phân tích dữ liệu offline

```powershell
python scripts/offline_data_quality_report.py
python scripts/offline_eda_analysis.py
python scripts/offline_model_evaluation.py
```

Output:

- `outputs/reports/data_quality_report.json`
- `outputs/reports/data_quality_report.md`
- `outputs/reports/eda_summary.json`
- `outputs/reports/eda_summary.md`
- `outputs/reports/model_evaluation.json`
- `outputs/reports/model_evaluation.md`
- `outputs/charts/rating_distribution.png`
- `outputs/charts/top_ingredients.png`
- `outputs/charts/difficulty_distribution.png`
- `outputs/charts/dietary_distribution.png`
- `outputs/charts/cooking_time_distribution.png`

## 4. Chạy pipeline không crawl

```powershell
python main.py --skip-crawl
```

Lệnh này dùng database đã có, không truy cập web. Kết quả mong đợi:

- Database có 1146 recipes.
- Huấn luyện Naive Bayes và Logistic Regression cho Vegetarian, Vegan, Gluten-free.
- Build TF-IDF search index.
- Tạo chart trong `charts/`.

## 5. Chạy crawl khi cần cập nhật dữ liệu

```powershell
python main.py
```

Lưu ý: crawl phụ thuộc internet và cấu trúc HTML/JSON-LD của BBC Good Food, nên kết quả có thể thay đổi theo thời điểm. Khi cần tái lập nhanh để chấm báo cáo, dùng các script offline ở mục 3.

## 6. Demo giao diện tùy chọn

Streamlit:

```powershell
streamlit run app.py
```

Flask API:

```powershell
python api.py
```

Hai phần này giúp xem kết quả và thử search, nhưng không phải trọng tâm đánh giá của project.

## 7. Metadata tái lập

- Database: `data/recipes.db`
- Recipes: 1146
- Ingredients: 12389
- Random seed: `RANDOM_STATE = 42` trong `config.py`
- Báo cáo chính: `DATA_ANALYSIS_REPORT.md`
- Ghi chú mô hình: `MODEL_EVALUATION_NOTES.md`
- Ghi chú cleaning thời gian: `DATA_CLEANING_NOTES.md`

## 8. Lưu ý về môi trường

`requirements.txt` dùng version range, chưa phải lockfile tuyệt đối. Nếu cần tái lập chặt hơn, tạo môi trường sạch và xuất lockfile riêng bằng:

```powershell
python -m pip freeze > requirements-lock.txt
```
