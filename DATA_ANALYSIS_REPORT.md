# DATA ANALYSIS REPORT

Nguồn số liệu: `outputs/reports/data_quality_report.json`, `outputs/reports/eda_summary.json`, `outputs/reports/model_evaluation.json`  
Ngày chạy: 2026-05-20  
Chế độ: offline, đọc SQLite `data/recipes.db`, không crawl web.

## 1. Mục tiêu và câu hỏi phân tích

Đây là báo cáo chính của project cho môn Lập trình trong phân tích dữ liệu. Trọng tâm là pipeline dữ liệu: thu thập, parse, làm sạch, kiểm tra chất lượng, EDA, trực quan hóa, TF-IDF search và đánh giá mô hình baseline.

Câu hỏi phân tích:

1. Dataset có quy mô và schema như thế nào?
2. Dữ liệu có thiếu, trùng lặp hoặc outlier đáng chú ý không?
3. Nguyên liệu, rating, độ khó và nhãn ăn kiêng phân bố ra sao?
4. Outlier thời gian `176986657` ảnh hưởng thế nào đến thống kê và biểu đồ?
5. TF-IDF search và các mô hình phân loại nhãn ăn kiêng hoạt động ra sao?
6. Kết quả có thể tái lập bằng script offline không?

## 2. Dữ liệu và schema

Database thật có 2 bảng chính:

- `recipes`: thông tin công thức, URL, thời gian chuẩn bị/nấu, rating, difficulty, dietary labels, raw ingredients, instruction, description, image URL.
- `ingredients`: danh sách nguyên liệu đã làm sạch, liên kết với `recipes.recipe_id`.

Tổng quan:

| Chỉ số | Giá trị |
|---|---:|
| Tổng recipes | 1146 |
| Tổng ingredients | 12389 |
| Recipe thiếu title | 0 |
| Recipe thiếu URL | 0 |
| Recipe thiếu rating | 257 |
| Recipe thiếu prep_time_min | 0 |
| Recipe thiếu cook_time_min | 1 |
| URL trùng | 0 extra rows |
| Title trùng | 2 extra rows |
| Recipe không có ingredient | 0 |

Nhận xét: dataset đủ lớn cho đồ án môn học và khóa URL khá sạch. Rating thiếu 257/1146 mẫu, vì vậy các kết luận về rating chỉ áp dụng cho 889 recipe có rating.

## 3. Chất lượng dữ liệu

Các kiểm tra chính trong `offline_data_quality_report.py`:

- Missing values cho title, URL, rating, prep/cook time.
- Duplicate URL/title.
- Recipe không có ingredient.
- Distribution của difficulty và dietary labels.
- Raw time stats và valid-only time stats.
- Top invalid/outlier records cho các cột thời gian.

Kết quả đáng chú ý:

- URL không trùng, phù hợp làm định danh nguồn.
- Có 2 title trùng, cần hiểu là công thức khác cùng tên hoặc duplicate nội dung.
- Không có recipe nào mất hoàn toàn ingredient.
- Có lỗi cleaning nguyên liệu như `emon juiced`, `arlic cloves crushed`; đây là hạn chế regex, ảnh hưởng một phần đến TF-IDF và ML.

## 4. Xử lý outlier thời gian

Database chỉ có 2 cột thời gian:

- `prep_time_min`
- `cook_time_min`

Không có `total_time` hoặc `total_time_min`.

Raw time stats:

| Field | Count | Mean | Median | Min | Max |
|---|---:|---:|---:|---:|---:|
| prep_time_min | 1146 | 1389965.6981 | 15.0 | 1.0 | 176986657.0 |
| cook_time_min | 1145 | 14220803.4987 | 30.0 | 1.0 | 176986657.0 |

Giá trị `176986657` không thể là số phút nấu hợp lệ. Nếu đưa trực tiếp vào mean hoặc histogram, dữ liệu hợp lệ trong khoảng vài phút đến vài giờ sẽ bị nén lại và biểu đồ mất ý nghĩa.

Project dùng `normalize_duration_minutes()` với ngưỡng hợp lệ `0..1440` phút. Ngưỡng một ngày đủ rộng cho công thức nấu ăn, nhưng loại bỏ các số vô lý.

Valid-only time stats:

| Field | Valid count | Invalid count | Outlier count | Mean valid | Median valid | Max valid |
|---|---:|---:|---:|---:|---:|---:|
| prep_time_min | 1137 | 0 | 9 | 18.2735 | 15.0 | 180 |
| cook_time_min | 1053 | 0 | 92 | 45.1681 | 30.0 | 720 |

Biểu đồ `outputs/charts/cooking_time_distribution.png` đã loại 101 outlier khỏi phần vẽ. Báo cáo vẫn giữ raw stats để truy vết nguồn lỗi, nhưng phân tích dùng valid-only stats.

Giả thuyết nguyên nhân: một số recipe thiếu hoặc không có cook-time rõ ràng, parser fallback cũ tìm text cha chứa `prep`/`cook` rồi bắt nhầm một số lớn từ vùng text khác của trang. Code hiện tại chặn dữ liệu mới bằng normalization trước khi lưu vào DB.

## 5. EDA và nhận xét biểu đồ

### Nguyên liệu phổ biến

Top 10 nguyên liệu:

| Ingredient | Count |
|---|---:|
| olive oil | 228 |
| plain flour | 177 |
| caster sugar | 171 |
| eggs | 139 |
| butter | 121 |
| vanilla extract | 121 |
| vegetable oil | 112 |
| double cream | 109 |
| milk | 107 |
| baking powder | 101 |

Biểu đồ: `outputs/charts/top_ingredients.png`

Nhận xét: nhóm nguyên liệu nền như dầu, bột, đường, trứng, bơ xuất hiện nhiều, phản ánh dataset có nhiều món nướng và món tráng miệng.

### Difficulty

| Difficulty | Count |
|---|---:|
| Easy | 1010 |
| More effort | 112 |
| Unknown | 15 |
| A challenge | 6 |
| Medium | 3 |

Biểu đồ: `outputs/charts/difficulty_distribution.png`

Nhận xét: dữ liệu lệch mạnh về `Easy`. Vì vậy không nên dùng dataset này để kết luận sâu về nhóm món khó nếu chưa bổ sung dữ liệu.

### Dietary labels

| Label | Count |
|---|---:|
| Vegetarian | 569 |
| Egg-Free | 286 |
| Gluten-Free | 260 |
| Nut-Free | 247 |
| Dairy-Free | 181 |
| Vegan | 123 |

Biểu đồ: `outputs/charts/dietary_distribution.png`

Nhận xét: dietary labels là multi-label và mất cân bằng. Nhãn Vegan chỉ có 123 positive, làm recall của mô hình thấp.

### Rating

| Metric | Value |
|---|---:|
| count | 889 |
| mean | 4.3781 |
| median | 4.5 |
| min | 1.0 |
| max | 5.0 |

Biểu đồ: `outputs/charts/rating_distribution.png`

Nhận xét: rating tập trung cao, median 4.5. Có thể có thiên lệch vì các công thức ít rating hoặc không rating bị thiếu khỏi thống kê rating.

### Cooking time

Biểu đồ: `outputs/charts/cooking_time_distribution.png`

Nhận xét: biểu đồ dùng các giá trị đã lọc `0..1440` phút. Điều này cần thiết vì raw max `176986657` làm histogram và mean không còn diễn giải được.

## 6. TF-IDF search

TF-IDF biến nguyên liệu thành vector văn bản, sau đó dùng Cosine Similarity để xếp hạng recipe theo query nguyên liệu.

Kết quả offline:

- Search index dùng 1146 recipes.
- Số feature TF-IDF tối đa: 5000.
- Đây là mô hình search baseline phù hợp cho môn học vì dễ giải thích, tái lập và gắn trực tiếp với dữ liệu nguyên liệu đã làm sạch.

Hạn chế:

- Không hiểu synonym hoặc typo.
- Phụ thuộc mạnh vào chất lượng cleaning nguyên liệu.
- Query quá chung có thể cho kết quả ít phân biệt.

## 7. Đánh giá mô hình phân loại

Mô hình phân loại nhãn Vegetarian, Vegan, Gluten-free dùng text nguyên liệu làm feature.

Kết quả tóm tắt:

| Label | Model | Accuracy | Precision | Recall | F1 |
|---|---|---:|---:|---:|---:|
| Vegetarian | Naive Bayes | 0.7870 | 0.8571 | 0.6842 | 0.7610 |
| Vegetarian | Logistic Regression | 0.8043 | 0.8000 | 0.8070 | 0.8035 |
| Vegan | Naive Bayes | 0.8957 | 0.5714 | 0.1600 | 0.2500 |
| Vegan | Logistic Regression | 0.9130 | 0.7778 | 0.2800 | 0.4118 |
| Gluten-free | Naive Bayes | 0.8087 | 0.5957 | 0.5283 | 0.5600 |
| Gluten-free | Logistic Regression | 0.8609 | 0.7234 | 0.6415 | 0.6800 |

Nhận xét:

- Logistic Regression tốt hơn Naive Bayes ở cả ba nhãn theo F1.
- Vegan có accuracy cao nhưng recall thấp, do dữ liệu mất cân bằng: negative nhiều hơn positive.
- Vì đây là multi-label classification được tách thành từng bài toán nhị phân, cần đọc precision/recall/F1 thay vì chỉ nhìn accuracy.

## 8. Output chính

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

## 9. Hạn chế dữ liệu và hướng cải thiện

1. Dataset phụ thuộc vào cấu trúc BBC Good Food tại thời điểm crawl.
2. Rating thiếu 257 dòng, có thể gây thiên lệch khi phân tích rating.
3. Dietary labels có thể thiếu, không nhất quán hoặc nhiễu.
4. Vegan là lớp mất cân bằng, cần class weight, threshold tuning hoặc bổ sung dữ liệu nếu muốn cải thiện recall.
5. Cleaning nguyên liệu còn lỗi regex, ảnh hưởng đến cả EDA, TF-IDF và classifier.
6. DB cũ vẫn giữ raw outlier thời gian để truy vết; phân tích hiện dùng valid-only stats.
7. Chưa có đánh giá search bằng ground truth thủ công, mới đánh giá ở mức sanity check/sample query.
