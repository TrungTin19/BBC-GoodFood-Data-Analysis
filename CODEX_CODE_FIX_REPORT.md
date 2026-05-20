# CODEX CODE FIX REPORT

Ngày thực hiện: 2026-05-19  
Chế độ: sửa code thật, test thật, pipeline offline, không crawl web.

## 1. Tóm tắt thay đổi

Đã bổ sung lớp phân tích dữ liệu offline, EDA chart, đánh giá ML offline và test pytest mới. Một số chỉnh sửa kỹ thuật nhỏ cho API/model loading được giữ ở mức phụ trợ để app demo chạy ổn định, không phải trọng tâm của đề tài.

## 2. File đã thêm

| File | Lý do |
|---|---|
| `scripts/__init__.py` | Biến `scripts/` thành package importable ổn định cho pytest. |
| `scripts/offline_data_quality_report.py` | Tạo report chất lượng dữ liệu JSON/Markdown từ SQLite offline. |
| `scripts/offline_eda_analysis.py` | Tạo EDA chart và diễn giải ngắn cho từng biểu đồ. |
| `scripts/offline_model_evaluation.py` | Đánh giá TF-IDF search index và classification offline. |
| `tests/test_data_quality_report.py` | Test script data quality tạo output và không crash khi thiếu cột. |
| `tests/test_eda_analysis.py` | Test EDA tạo report/chart và xử lý DB thiếu. |
| `tests/test_model_evaluation.py` | Test model evaluation tạo output, skip dataset nhỏ, kiểm path model trusted. |
| `tests/test_api_validation.py` | Test Flask API reject input sai bằng HTTP 400. |
| `DATA_ANALYSIS_REPORT.md` | Báo cáo phân tích dữ liệu dựa trên output thật. |
| `REPRODUCIBILITY.md` | Lệnh Windows tái lập test, scripts, pipeline, Streamlit, Flask. |
| `SECURITY_CHECKLIST.md` | Phụ lục kỹ thuật ngắn cho app demo; không phải trọng tâm phân tích dữ liệu. |
| `MODEL_EVALUATION_NOTES.md` | Giải thích các khái niệm ML, file/hàm áp dụng, tác dụng, hạn chế. |
| `CODEX_CODE_FIX_REPORT.md` | Báo cáo kết quả sửa code và chạy lệnh. |

## 3. File đã sửa

| File | Lý do sửa |
|---|---|
| `api.py` | Thêm validation tham số cơ bản cho app demo: query không rỗng, giới hạn độ dài, phân trang và `top_n` hợp lý. |
| `ml_search.py` | Chuẩn hóa đường dẫn model nội bộ khi lưu/tải model cho phần đánh giá và demo. |

Không sửa/xóa file cũ khác. `CODEX_FULL_AUDIT_REPORT.md` từ audit trước được giữ nguyên.

## 4. Kết quả lệnh đã chạy

| Lệnh | Kết quả | Ghi chú |
|---|---|---|
| `python -m compileall .` | PASS | Compile toàn bộ `.py`, gồm scripts/tests mới. |
| `python -m pytest -q` | PASS | `44 passed in 2.01s`. |
| `python test_all.py` | PASS | `Ran 31 tests in 0.749s`, `OK`. |
| `python scripts/offline_data_quality_report.py` | PASS | Tạo `data_quality_report.json/md`, status `ok`. |
| `python scripts/offline_eda_analysis.py` | PASS | Tạo `eda_summary.json/md` và 5 chart PNG, status `ok`. |
| `python scripts/offline_model_evaluation.py` | PASS | Tạo `model_evaluation.json/md`, status `ok`. |
| `python main.py --skip-crawl` | PASS | Không crawl; train ML, build TF-IDF, tạo chart trong `charts/`. |

Lệnh fail trong quá trình làm:

| Lệnh | Fail | Nguyên nhân | Cách xử lý |
|---|---|---|---|
| `python -m pytest -q` lần đầu | FAIL | `scripts/` chưa có `__init__.py`, import `scripts.offline_*` fail. | Thêm `scripts/__init__.py`; chạy lại pytest PASS 44 tests. |

## 5. Output đã tạo

Reports:

- `outputs/reports/data_quality_report.json`
- `outputs/reports/data_quality_report.md`
- `outputs/reports/eda_summary.json`
- `outputs/reports/eda_summary.md`
- `outputs/reports/model_evaluation.json`
- `outputs/reports/model_evaluation.md`

Charts:

- `outputs/charts/rating_distribution.png`
- `outputs/charts/top_ingredients.png`
- `outputs/charts/difficulty_distribution.png`
- `outputs/charts/dietary_distribution.png`
- `outputs/charts/cooking_time_distribution.png`

## 6. Kết quả phân tích thật

Data quality:

- Recipes: 1146
- Ingredients: 12389
- Missing rating: 257
- Missing cook_time_min: 1
- URL duplicate extra rows: 0
- Title duplicate extra rows: 2
- Recipes without ingredients: 0
- Rating mean/median: 4.3781 / 4.5
- Time outlier nghiêm trọng: nhiều giá trị `176986657` ở `prep_time_min` hoặc `cook_time_min`.

EDA:

- Rating tập trung cao, median 4.50.
- `olive oil` là ingredient phổ biến nhất với 228 lần.
- Difficulty lệch mạnh về `Easy` với 1010/1146 recipe.
- Dietary labels multi-label và mất cân bằng.
- Cooking-time chart đã lọc giá trị âm và >300 phút để tránh outlier phá biểu đồ.

ML:

- Search index: 1146 recipes, 5000 TF-IDF features.
- Vegetarian Logistic Regression: accuracy 0.8043, F1 0.8035.
- Vegan Logistic Regression: accuracy 0.9130 nhưng recall 0.2800, F1 0.4118.
- Gluten-free Logistic Regression: accuracy 0.8609, F1 0.6800.

## 7. Checklist cuối

| Hạng mục | Trạng thái | Ghi chú |
|---|---|---|
| Code added | PASS | Thêm 3 script offline và package `scripts`. |
| Tests added | PASS | Thêm 13 pytest mới, tổng pytest 44 pass. |
| Tests run | PASS | `compileall`, `pytest`, `test_all.py` đều pass. |
| Data quality analysis | PASS | JSON/MD report tạo từ DB thật. |
| EDA charts | PASS | 5 chart PNG trong `outputs/charts`. |
| ML evaluation | PASS | Search + NB/LR metrics offline; có ghi hạn chế. |
| App demo technical checks | PARTIAL | Chỉ giữ validation/path check cơ bản; không mở rộng thành đề tài security/backend. |
| Reproducibility docs | PASS | Có `REPRODUCIBILITY.md` với lệnh Windows. |

## 8. Follow-up: time cleaning update

Sau báo cáo này, đã có lượt sửa riêng cho vấn đề outlier thời gian:

- Thêm `parser.normalize_duration_minutes()` với ngưỡng hợp lệ `0..1440` phút.
- `database.insert_recipe()` dùng normalization trước khi lưu `prep_time_min` và `cook_time_min`.
- `offline_data_quality_report.py` xuất thêm `time_stats_raw`, `time_stats_valid_only`, `time_quality`.
- `offline_eda_analysis.py` loại outlier >1440 khỏi `cooking_time_distribution.png` và ghi số outlier bị loại.
- Thêm `tests/test_time_normalization.py`.

Kết quả mới:

- `prep_time_min`: 1137 valid, 9 outlier, max valid 180.
- `cook_time_min`: 1053 valid, 92 outlier, max valid 720.
- EDA loại tổng cộng 101 outlier khỏi biểu đồ thời gian.

## 9. Hạn chế còn lại theo phạm vi phân tích dữ liệu

1. Dữ liệu thời gian cũ vẫn giữ outlier trong DB gốc để truy vết; phân tích đã dùng valid-only stats.
2. Cleaning nguyên liệu còn lỗi cắt chữ đầu (`emon`, `arlic`), ảnh hưởng search/ML.
3. Nhãn ăn kiêng có thể nhiễu hoặc mất cân bằng, đặc biệt nhãn Vegan.
4. `requirements.txt` chưa có lockfile, nên tái lập tuyệt đối còn phụ thuộc môi trường Python.
