# CODEX TIME CLEANING FIX REPORT

Ngày thực hiện: 2026-05-20  
Mục tiêu: xử lý nghiêm túc outlier thời gian `176986657` trong pipeline phân tích dữ liệu.

## 1. File đã đọc

- `parser.py`
- `crawler.py`
- `database.py`
- `seed_data.py`
- `scripts/offline_data_quality_report.py`
- `scripts/offline_eda_analysis.py`
- `scripts/offline_model_evaluation.py`
- `tests/`
- `DATA_ANALYSIS_REPORT.md`
- `CODEX_CODE_FIX_REPORT.md`

## 2. Truy vết outlier

Schema thực tế của `recipes` có các cột thời gian:

- `prep_time_min INTEGER`
- `cook_time_min INTEGER`

Không có `total_time` hoặc `total_time_min`.

Kết quả truy vấn SQLite:

- `prep_time_min`: 9 dòng có giá trị >1440, tất cả là `176986657`.
- `cook_time_min`: 92 dòng có giá trị >1440, tất cả là `176986657`.
- Không có giá trị âm trong DB thật.

Ví dụ record liên quan:

| recipe_id | title | url | cột lỗi | value |
|---:|---|---|---|---:|
| 22 | Campari soda & blood orange pitcher | https://www.bbcgoodfood.com/recipes/campari-soda-blood-orange-pitcher | cook_time_min | 176986657 |
| 59 | Tamales | https://www.bbcgoodfood.com/recipes/tamales | prep_time_min, cook_time_min | 176986657 |
| 213 | Homemade kimchi | https://www.bbcgoodfood.com/recipes/homemade-kimchi | prep_time_min, cook_time_min | 176986657 |
| 821 | Chilli con carne recipe | https://www.bbcgoodfood.com/recipes/chilli-con-carne-recipe | prep_time_min | 176986657 |
| 1041 | Easy lemonade | https://www.bbcgoodfood.com/recipes/really-easy-lemonade | prep_time_min, cook_time_min | 176986657 |
| 1080 | Lemon drizzle cake | https://www.bbcgoodfood.com/recipes/lemon-drizzle-cake | prep_time_min | 176986657 |
| 1094 | Roasted cauliflower | https://www.bbcgoodfood.com/recipes/roasted-cauliflower | prep_time_min | 176986657 |

## 3. Nguyên nhân hoặc giả thuyết nguyên nhân

Không crawl web thật theo yêu cầu nên không kiểm HTML live. Dựa trên code và pattern dữ liệu, nguyên nhân hợp lý là parser fallback cũ tìm text cha chứa `prep`/`cook`, rồi regex bắt nhầm số lớn từ vùng text khác của trang. Nhiều record lỗi là đồ uống, salad, sauce, sandwich hoặc món có thể thiếu cook-time/no-cook.

`176986657` không thể là phút nấu hợp lệ. Đây là outlier dữ liệu, không phải thông tin công thức.

## 4. Logic cleaning mới

Thêm `normalize_duration_minutes()` trong `parser.py`:

- Hỗ trợ text thường: `"10 mins"`, `"1 hr"`, `"1 hr 30 mins"`, `"2 hours"`.
- Hỗ trợ ISO 8601 duration: `"PT1H30M"`.
- Hỗ trợ số phút dạng int/float hoặc chuỗi số.
- Giá trị hợp lệ: `0..1440` phút.
- Giá trị âm, rỗng, không parse được hoặc >1440 phút trả `None`.

Tích hợp:

- `parse_time_to_minutes()` gọi `normalize_duration_minutes()`.
- `_parse_iso_duration()` có anchor regex chặt hơn và cũng áp ngưỡng 1440.
- `database.insert_recipe()` normalize `prep_time_min` và `cook_time_min` trước khi lưu.
- `offline_data_quality_report.py` báo raw stats, valid-only stats và `time_quality`.
- `offline_eda_analysis.py` loại invalid/outlier khỏi `cooking_time_distribution.png`.

## 5. File đã sửa/thêm

File sửa:

- `parser.py`
- `database.py`
- `scripts/offline_data_quality_report.py`
- `scripts/offline_eda_analysis.py`
- `tests/test_data_quality_report.py`
- `tests/test_eda_analysis.py`
- `DATA_ANALYSIS_REPORT.md`
- `CODEX_CODE_FIX_REPORT.md`

File thêm:

- `tests/test_time_normalization.py`
- `DATA_CLEANING_NOTES.md`
- `CODEX_TIME_CLEANING_FIX_REPORT.md`

## 6. Kết quả chạy lệnh

| Lệnh | Kết quả | Ghi chú |
|---|---|---|
| `python -m compileall .` | PASS | Compile toàn bộ repo. |
| `python -m pytest -q` | PASS | `48 passed in 3.73s`. |
| `python test_all.py` | PASS | `Ran 31 tests in 0.751s`, `OK`. |
| `python scripts/offline_data_quality_report.py` | PASS | Tạo lại JSON/MD report, status `ok`. |
| `python scripts/offline_eda_analysis.py` | PASS | Tạo lại EDA JSON/MD và chart, status `ok`. |
| `python scripts/offline_model_evaluation.py` | PASS | Tạo lại model evaluation JSON/MD, status `ok`. |
| `python main.py --skip-crawl` | PASS | Không crawl; ML/charts chạy thành công trong 5.3s. |

Lần chạy xác nhận mới nhất: 2026-05-20.

## 7. Kết quả scripts sau xử lý

`outputs/reports/data_quality_report.json`:

| Field | Valid | Invalid | Outlier | Max valid | Threshold |
|---|---:|---:|---:|---:|---:|
| `prep_time_min` | 1137 | 0 | 9 | 180 | 1440 |
| `cook_time_min` | 1053 | 0 | 92 | 720 | 1440 |

Valid-only stats:

| Field | Count | Mean | Median | Min | Max |
|---|---:|---:|---:|---:|---:|
| `prep_time_min` | 1137 | 18.2735 | 15.0 | 1.0 | 180.0 |
| `cook_time_min` | 1053 | 45.1681 | 30.0 | 1.0 | 720.0 |

`outputs/reports/eda_summary.json`:

- Cooking-time chart excludes values above 1440 minutes.
- Excluded outliers: 101.
- Other invalid values: 0.

## 8. Vì sao không đưa outlier vào biểu đồ/trung bình

Raw mean bị phá hỏng bởi `176986657`:

- Raw `prep_time_min` mean: `1389965.6981`
- Valid-only `prep_time_min` mean: `18.2735`
- Raw `cook_time_min` mean: `14220803.4987`
- Valid-only `cook_time_min` mean: `45.1681`

Nếu đưa outlier vào histogram, phần lớn dữ liệu hợp lệ 1..180 phút sẽ bị nén về một vùng nhỏ và biểu đồ không còn có ý nghĩa phân tích.

## 9. Checklist cuối

| Hạng mục | Trạng thái |
|---|---|
| Đọc code và truy vết DB | PASS |
| Xác định cột chứa `176986657` | PASS |
| Thêm normalization function | PASS |
| Chặn dữ liệu mới lưu outlier vào DB | PASS |
| Data quality report có valid/invalid/outlier count | PASS |
| EDA loại outlier khỏi chart và ghi lý do | PASS |
| Test normalization | PASS |
| Test report/EDA với outlier | PASS |
| Chạy toàn bộ lệnh bắt buộc | PASS |
| Cập nhật tài liệu | PASS |

## 10. Rủi ro còn lại

1. DB cũ vẫn giữ raw outlier để truy vết. Nếu muốn làm sạch vật lý, cần migration có backup.
2. Chưa xác minh HTML live vì yêu cầu không crawl web thật.
3. Cleaning nguyên liệu vẫn còn lỗi `emon`/`arlic`, nằm ngoài phạm vi time cleaning.
