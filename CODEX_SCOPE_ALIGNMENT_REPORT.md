# CODEX SCOPE ALIGNMENT REPORT

Ngày thực hiện: 2026-05-20  
Mục tiêu: rà soát và chỉnh tài liệu để project đúng phạm vi môn Lập trình trong phân tích dữ liệu.

## 1. File đã đọc

- `README.md`
- `DATA_ANALYSIS_REPORT.md`
- `MODEL_EVALUATION_NOTES.md`
- `REPRODUCIBILITY.md`
- `SECURITY_CHECKLIST.md`
- `CODEX_CODE_FIX_REPORT.md`
- `CODEX_TIME_CLEANING_FIX_REPORT.md`

## 2. File đã chỉnh

| File | Nội dung chỉnh |
|---|---|
| `README.md` | Viết lại theo hướng data pipeline, data quality, data cleaning, EDA, visualization, TF-IDF/search, model evaluation và reproducibility. API/Streamlit được đặt là demo phụ trợ. |
| `DATA_ANALYSIS_REPORT.md` | Viết lại thành tài liệu chính: câu hỏi phân tích, dữ liệu/schema, chất lượng dữ liệu, outlier thời gian, EDA, nhận xét biểu đồ, TF-IDF, model evaluation và hạn chế dữ liệu. |
| `MODEL_EVALUATION_NOTES.md` | Chỉnh theo hướng môn học: giải thích TF-IDF, Cosine Similarity, Naive Bayes, Logistic Regression, train/test, metrics, class imbalance và noisy labels. |
| `REPRODUCIBILITY.md` | Giữ các lệnh tái lập offline: pytest, data quality, EDA, model evaluation, pipeline `--skip-crawl`; đưa app/API xuống phần demo tùy chọn. |
| `SECURITY_CHECKLIST.md` | Đổi thành phụ lục kỹ thuật ngắn, ghi rõ không phải trọng tâm đề tài và không mở rộng DevOps/security. |
| `CODEX_CODE_FIX_REPORT.md` | Giảm nhấn mạnh security/backend, chuyển thành ghi chú kỹ thuật phụ trợ cho app demo; phần rủi ro còn lại tập trung vào dữ liệu, cleaning, labels và reproducibility. |
| `CODEX_SCOPE_ALIGNMENT_REPORT.md` | Thêm báo cáo cuối cho lần rà soát phạm vi. |

## 3. Phần đã giảm hoặc giữ

Đã giảm:

- Mô tả REST API như một thành phần trọng tâm.
- Nội dung security/backend/DevOps trong README và report.
- Checklist security kiểu Critical/High/Medium/Low gây lệch trọng tâm.
- Các khuyến nghị như bandit, pip-audit, rate limiting, deployment trong tài liệu tái lập chính.

Đã giữ:

- Pipeline thu thập, parse, SQLite và offline scripts.
- Data quality report và xử lý outlier thời gian.
- EDA và biểu đồ.
- TF-IDF search.
- Đánh giá Naive Bayes/Logistic Regression.
- Reproducibility bằng lệnh offline.
- Phụ lục kỹ thuật ngắn cho app demo, nhưng không đặt làm trọng tâm.

## 4. Vì sao project đúng phạm vi môn học

Project hiện bám đúng các năng lực của môn Lập trình trong phân tích dữ liệu:

1. Có pipeline dữ liệu rõ ràng từ crawl/parse đến SQLite.
2. Có bước làm sạch dữ liệu cụ thể, đặc biệt normalization thời gian và cleaning nguyên liệu.
3. Có kiểm tra chất lượng dữ liệu bằng script offline và output JSON/Markdown.
4. Có EDA và trực quan hóa bằng biểu đồ.
5. Có xử lý outlier thời gian để tránh làm sai mean/histogram.
6. Có TF-IDF search để minh họa xử lý dữ liệu text.
7. Có đánh giá mô hình bằng train/test, cross-validation và các metrics cơ bản.
8. Có tài liệu tái lập kết quả bằng các lệnh offline.

## 5. Kết quả lệnh đã chạy

| Lệnh | Kết quả |
|---|---|
| `python -m pytest -q` | PASS, `48 passed in 2.43s` |
| `python scripts/offline_data_quality_report.py` | PASS, status `ok`, tạo `outputs/reports/data_quality_report.json/md` |
| `python scripts/offline_eda_analysis.py` | PASS, status `ok`, tạo `outputs/reports/eda_summary.json/md` |
| `python scripts/offline_model_evaluation.py` | PASS, status `ok`, tạo `outputs/reports/model_evaluation.json/md` |

## 6. Checklist sẵn sàng push

| Mục | Trạng thái |
|---|---|
| Đọc đủ tài liệu yêu cầu | PASS |
| Không thêm chức năng mới | PASS |
| Không mở rộng security/DevOps | PASS |
| README nhấn mạnh phạm vi môn học | PASS |
| `DATA_ANALYSIS_REPORT.md` là tài liệu phân tích chính | PASS |
| `MODEL_EVALUATION_NOTES.md` giải thích thuật toán theo hướng môn học | PASS |
| `REPRODUCIBILITY.md` giữ lệnh offline | PASS |
| `SECURITY_CHECKLIST.md` chuyển thành phụ lục kỹ thuật ngắn | PASS |
| Chạy lại pytest và 3 script offline | PASS |
| Sẵn sàng commit/push Git | PASS |
