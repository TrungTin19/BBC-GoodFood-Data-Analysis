# TECHNICAL APPENDIX: BASIC SAFETY NOTES

Tài liệu này chỉ là phụ lục kỹ thuật ngắn. Nó không phải trọng tâm của đề tài. Trọng tâm project vẫn là thu thập dữ liệu, làm sạch dữ liệu, data quality, EDA, trực quan hóa, TF-IDF/search, đánh giá mô hình và tái lập kết quả.

## Phạm vi

Các ghi chú dưới đây nhằm đảm bảo app demo không có lỗi kỹ thuật cơ bản khi chạy local:

- Không nhận file/model path tùy ý từ user.
- Giới hạn tham số API đơn giản như `q`, `top_n`, `page`, `per_page`.
- Chỉ load model nội bộ trong `data/models`.
- Dùng parameterized query trong các truy vấn có input.

## Những điểm đã ghi nhận

| Mục | Trạng thái | Ghi chú |
|---|---|---|
| API input validation | Đã có mức cơ bản | Query không rỗng, giới hạn độ dài và phân trang. |
| Model path handling | Đã có mức cơ bản | `joblib.load` chỉ dùng model path nội bộ. |
| SQLite query parameters | Đã dùng ở các truy vấn có input | Phù hợp app local/demo. |
| CORS local demo | Giới hạn cho môi trường local | Không xem là phần phân tích dữ liệu. |

## Không mở rộng trong đồ án này

Các nội dung sau không được xem là trọng tâm môn học và không mở rộng thêm trong lần rà soát này:

- DevOps/CI/CD.
- Security audit chuyên sâu.
- Rate limiting production.
- Dependency audit bắt buộc.
- Deployment cloud.

## Liên hệ với báo cáo chính

Khi trình bày đồ án, chỉ nên nhắc phụ lục này nếu được hỏi về app demo. Báo cáo chính cần ưu tiên:

1. Data pipeline.
2. Data cleaning và outlier handling.
3. Data quality report.
4. EDA và visualization.
5. TF-IDF/search.
6. Model evaluation.
7. Reproducibility.
