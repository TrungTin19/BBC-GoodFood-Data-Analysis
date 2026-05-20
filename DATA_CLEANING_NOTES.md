# DATA CLEANING NOTES - TIME DURATION

Ngày cập nhật: 2026-05-20  
Phạm vi: xử lý outlier thời gian nấu trong pipeline phân tích dữ liệu offline.

## 1. Phát hiện

`scripts/offline_data_quality_report.py` phát hiện giá trị `176986657` trong các cột thời gian:

| Cột | Valid count | Invalid count | Outlier count | Max valid | Raw max |
|---|---:|---:|---:|---:|---:|
| `prep_time_min` | 1137 | 0 | 9 | 180 | 176986657 |
| `cook_time_min` | 1053 | 0 | 92 | 720 | 176986657 |

Ví dụ record liên quan:

- `recipe_id=22`, `Campari soda & blood orange pitcher`, `https://www.bbcgoodfood.com/recipes/campari-soda-blood-orange-pitcher`, `cook_time_min=176986657`
- `recipe_id=59`, `Tamales`, `https://www.bbcgoodfood.com/recipes/tamales`, `prep_time_min=176986657`, `cook_time_min=176986657`
- `recipe_id=213`, `Homemade kimchi`, `https://www.bbcgoodfood.com/recipes/homemade-kimchi`, `prep_time_min=176986657`, `cook_time_min=176986657`
- `recipe_id=1041`, `Easy lemonade`, `https://www.bbcgoodfood.com/recipes/really-easy-lemonade`, `prep_time_min=176986657`, `cook_time_min=176986657`
- `recipe_id=1080`, `Lemon drizzle cake`, `https://www.bbcgoodfood.com/recipes/lemon-drizzle-cake`, `prep_time_min=176986657`

## 2. Nguyên nhân hoặc giả thuyết nguyên nhân

Không crawl lại web trong lần sửa này, nên không xác minh HTML live. Dựa trên pattern dữ liệu, phần lớn outlier nằm ở các món có thể không cần nấu, đồ uống, salad, sauce hoặc món thiếu `cookTime`. Giả thuyết hợp lý là fallback parser cũ tìm text cha chứa chữ `cook`/`prep`, sau đó regex bắt nhầm số lớn từ vùng text khác của trang thay vì duration thật.

Giá trị `176986657` không phải phút hợp lệ. Nếu quy đổi ra phút, nó tương đương hơn 336 năm, nên chắc chắn là lỗi parse hoặc dữ liệu bẩn.

## 3. Cách xử lý trong code

Đã thêm `normalize_duration_minutes()` trong `parser.py`:

- Hỗ trợ `"10 mins"` -> `10`
- Hỗ trợ `"1 hr"` -> `60`
- Hỗ trợ `"1 hr 30 mins"` -> `90`
- Hỗ trợ `"PT1H30M"` -> `90`
- Hỗ trợ số nguyên phút nếu nằm trong ngưỡng hợp lệ
- Trả `None` cho `None`, chuỗi rỗng, số âm, số quá lớn hoặc text không parse được

Ngưỡng hợp lệ hiện tại: `0..1440` phút. Một ngày là ngưỡng rộng cho công thức nấu ăn, nhưng vẫn loại bỏ các số vô lý.

`database.insert_recipe()` cũng gọi normalization trước khi lưu, nên dữ liệu mới sẽ không còn lưu thời gian âm hoặc >1440 phút.

## 4. Ảnh hưởng đến phân tích dữ liệu

Không được dùng raw mean của thời gian vì outlier làm méo thống kê:

- Raw `prep_time_min` mean: `1389965.6981`
- Valid-only `prep_time_min` mean: `18.2735`
- Raw `cook_time_min` mean: `14220803.4987`
- Valid-only `cook_time_min` mean: `45.1681`

Biểu đồ `outputs/charts/cooking_time_distribution.png` hiện loại outlier >1440 và ghi rõ số lượng bị loại trong `outputs/reports/eda_summary.md`.

## 5. Tình trạng sau xử lý

Outlier trong DB cũ vẫn được giữ để truy vết nguồn dữ liệu, nhưng không còn được dùng trong valid-only stats và biểu đồ EDA. Dữ liệu mới đi qua `insert_recipe()` sẽ được normalize trước khi lưu.

Tóm tắt:

- `prep_time_min`: 1137 hợp lệ, 9 outlier, 0 invalid khác.
- `cook_time_min`: 1053 hợp lệ, 92 outlier, 0 invalid khác.
- Tổng outlier bị loại khỏi EDA cooking-time chart: 101.

## 6. Kiểm thử

Đã thêm `tests/test_time_normalization.py` để kiểm tra:

- `"10 mins" -> 10`
- `"1 hr" -> 60`
- `"1 hr 30 mins" -> 90`
- `"PT1H30M" -> 90`
- `-5 -> None`
- `176986657 -> None`
- `None -> None`
- `"" -> None`
- data quality report không crash khi có outlier
- EDA không crash khi có outlier
