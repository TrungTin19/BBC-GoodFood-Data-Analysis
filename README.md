# BBC GoodFood Data Analysis

Đồ án môn học: Lập trình trong phân tích dữ liệu  
Nguồn dữ liệu: BBC Good Food recipes  
Chế độ tái lập chính: offline với SQLite database và các script trong `scripts/`

## 1. Mục tiêu môn học

Project tập trung vào quy trình lập trình phục vụ phân tích dữ liệu:

- Thu thập URL và dữ liệu công thức từ BBC Good Food.
- Parse dữ liệu từ JSON-LD/HTML và lưu vào SQLite.
- Làm sạch nguyên liệu, thời gian nấu và nhãn chế độ ăn.
- Kiểm tra chất lượng dữ liệu: missing values, duplicate, outlier, schema.
- Phân tích khám phá dữ liệu (EDA) và trực quan hóa bằng Matplotlib/Seaborn.
- Xây dựng tìm kiếm công thức bằng TF-IDF và Cosine Similarity.
- Đánh giá mô hình phân loại nhãn ăn kiêng bằng Naive Bayes và Logistic Regression.
- Ghi lại cách chạy để tái lập kết quả.

API Flask và giao diện Streamlit chỉ là lớp demo để xem dữ liệu và kết quả; không phải trọng tâm của đề tài.

## 2. Câu hỏi phân tích

Project trả lời các câu hỏi chính:

1. Dataset thu được có bao nhiêu công thức, nguyên liệu, rating và nhãn ăn kiêng?
2. Dữ liệu có thiếu, trùng lặp hoặc outlier nào đáng chú ý không?
3. Nguyên liệu, độ khó, rating và nhãn ăn kiêng phân bố như thế nào?
4. Outlier thời gian nấu ảnh hưởng ra sao đến biểu đồ và thống kê trung bình?
5. TF-IDF có giúp tìm công thức theo nguyên liệu hợp lý không?
6. Naive Bayes và Logistic Regression phân loại Vegetarian, Vegan, Gluten-free tốt đến mức nào?
7. Kết quả có thể tái lập bằng các script offline hay không?

## 3. Dữ liệu hiện có

Theo `outputs/reports/data_quality_report.json`:

| Chỉ số | Giá trị |
|---|---:|
| Recipes | 1146 |
| Ingredients | 12389 |
| Missing rating | 257 |
| Missing cook_time_min | 1 |
| Duplicate URL extra rows | 0 |
| Duplicate title extra rows | 2 |
| Recipes without ingredients | 0 |

Vấn đề dữ liệu quan trọng đã xử lý trong báo cáo: outlier thời gian `176986657` ở `prep_time_min` và `cook_time_min`. Các thống kê và biểu đồ EDA dùng dữ liệu thời gian hợp lệ `0..1440` phút để tránh làm méo phân tích.

## 4. Cấu trúc project

```text
.
├── crawler.py                         # Thu thập URL công thức
├── parser.py                          # Parse và làm sạch dữ liệu
├── database.py                        # SQLite schema, insert, query, statistics
├── ml_search.py                       # TF-IDF search và mô hình phân loại
├── visualize.py                       # Biểu đồ cho pipeline chính
├── main.py                            # Điều phối pipeline
├── scripts/
│   ├── offline_data_quality_report.py # Báo cáo chất lượng dữ liệu
│   ├── offline_eda_analysis.py        # EDA và biểu đồ offline
│   └── offline_model_evaluation.py    # Đánh giá search/model offline
├── tests/                             # Pytest cho scripts, API validation, ML, cleaning
├── outputs/
│   ├── reports/                       # JSON/Markdown reports
│   └── charts/                        # EDA charts
├── DATA_ANALYSIS_REPORT.md            # Báo cáo phân tích dữ liệu chính
├── MODEL_EVALUATION_NOTES.md          # Giải thích thuật toán và metrics
└── REPRODUCIBILITY.md                 # Lệnh tái lập kết quả
```

## 5. Cài đặt

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Thư viện chính:

| Nhóm | Thư viện |
|---|---|
| Thu thập/parse | `requests`, `beautifulsoup4`, `lxml` |
| Dữ liệu | `pandas`, `numpy`, `sqlite3` |
| ML | `scikit-learn`, `joblib` |
| Trực quan hóa | `matplotlib`, `seaborn` |
| Demo app | `streamlit`, `flask`, `flask-cors` |

## 6. Chạy phân tích offline

Các lệnh quan trọng nhất cho môn học:

```powershell
python scripts/offline_data_quality_report.py
python scripts/offline_eda_analysis.py
python scripts/offline_model_evaluation.py
```

Output chính:

- `outputs/reports/data_quality_report.json`
- `outputs/reports/data_quality_report.md`
- `outputs/reports/eda_summary.json`
- `outputs/reports/eda_summary.md`
- `outputs/reports/model_evaluation.json`
- `outputs/reports/model_evaluation.md`
- `outputs/charts/*.png`

## 7. Chạy kiểm thử

```powershell
python -m pytest -q
python test_all.py
```

Pytest hiện có 48 tests, bao gồm kiểm tra normalization thời gian, data quality report, EDA, model evaluation và validation cơ bản.

## 8. Chạy pipeline

Chạy không crawl lại web:

```powershell
python main.py --skip-crawl
```

Chạy đầy đủ gồm crawl:

```powershell
python main.py
```

Lưu ý: crawl web mất thời gian và phụ thuộc cấu trúc trang BBC Good Food. Khi báo cáo/chấm bài, nên ưu tiên các script offline để tái lập kết quả nhanh và ổn định.

## 9. Phân tích và mô hình

### Data Quality

`scripts/offline_data_quality_report.py` kiểm tra:

- Tổng số dòng.
- Missing values.
- Duplicate title/URL.
- Recipe không có ingredient.
- Raw time stats và valid-only time stats.
- Valid/invalid/outlier count cho các cột thời gian.

### EDA và Visualization

`scripts/offline_eda_analysis.py` tạo:

- `rating_distribution.png`
- `top_ingredients.png`
- `difficulty_distribution.png`
- `dietary_distribution.png`
- `cooking_time_distribution.png`

Biểu đồ thời gian loại các giá trị `>1440` phút để outlier `176986657` không làm méo histogram và trung bình.

### TF-IDF Search

TF-IDF biến văn bản nguyên liệu thành vector. Cosine Similarity dùng để xếp hạng công thức gần nhất với query nguyên liệu.

### Model Evaluation

`scripts/offline_model_evaluation.py` đánh giá:

- Multinomial Naive Bayes.
- Logistic Regression.
- Accuracy, Precision, Recall, F1, Confusion Matrix.
- Cross-validation khi dữ liệu đủ điều kiện.

Kết quả cần đọc cùng hạn chế dữ liệu: nhãn Vegan mất cân bằng nên accuracy cao nhưng recall thấp.

## 10. Tài liệu chính

- `DATA_ANALYSIS_REPORT.md`: báo cáo phân tích dữ liệu chính.
- `MODEL_EVALUATION_NOTES.md`: giải thích thuật toán và metrics theo hướng môn học.
- `REPRODUCIBILITY.md`: lệnh tái lập kết quả.
- `DATA_CLEANING_NOTES.md`: ghi chú riêng về outlier thời gian.
- `SECURITY_CHECKLIST.md`: phụ lục kỹ thuật ngắn, không phải trọng tâm đề tài.

## 11. Hạn chế

- Dataset phụ thuộc HTML/JSON-LD của BBC Good Food tại thời điểm crawl.
- Nhãn ăn kiêng lấy từ tag/keyword nguồn, có thể thiếu hoặc không nhất quán.
- Cleaning nguyên liệu còn một số lỗi regex như mất chữ đầu trong vài nguyên liệu.
- DB hiện giữ raw outlier thời gian để truy vết, còn phân tích dùng valid-only stats.
- Mô hình ML là baseline cho môn học, chưa tuning sâu class imbalance hoặc threshold.
