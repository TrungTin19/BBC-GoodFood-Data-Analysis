# MODEL EVALUATION NOTES

Nguồn số liệu: `outputs/reports/model_evaluation.json`  
Dataset offline: 1146 recipes  
Phạm vi: giải thích thuật toán và chỉ số đánh giá theo hướng môn Lập trình trong phân tích dữ liệu.

## 1. Mục tiêu đánh giá

Phần model trong project có hai nhiệm vụ:

1. Tìm kiếm công thức theo nguyên liệu bằng TF-IDF và Cosine Similarity.
2. Phân loại nhãn ăn kiêng Vegetarian, Vegan, Gluten-free bằng mô hình text classification baseline.

Mục tiêu không phải xây dựng hệ thống production, mà là chứng minh khả năng lập trình pipeline phân tích dữ liệu: tạo feature từ text, huấn luyện mô hình, chia train/test, tính metric và diễn giải hạn chế.

## 2. Kết quả tóm tắt

| Label | Model | Accuracy | Precision | Recall | F1 | CV mean |
|---|---|---:|---:|---:|---:|---:|
| Vegetarian | Naive Bayes | 0.7870 | 0.8571 | 0.6842 | 0.7610 | 0.7282 |
| Vegetarian | Logistic Regression | 0.8043 | 0.8000 | 0.8070 | 0.8035 | 0.8013 |
| Vegan | Naive Bayes | 0.8957 | 0.5714 | 0.1600 | 0.2500 | 0.8897 |
| Vegan | Logistic Regression | 0.9130 | 0.7778 | 0.2800 | 0.4118 | 0.8886 |
| Gluten-free | Naive Bayes | 0.8087 | 0.5957 | 0.5283 | 0.5600 | 0.8166 |
| Gluten-free | Logistic Regression | 0.8609 | 0.7234 | 0.6415 | 0.6800 | 0.8362 |

Nhận xét chính: Logistic Regression có F1 tốt hơn Naive Bayes trong cả ba nhãn. Vegan có accuracy cao nhưng recall thấp, cho thấy mô hình bỏ sót nhiều recipe Vegan thật do class imbalance.

## 3. TF-IDF và Cosine Similarity

TF-IDF biến nguyên liệu thành vector số. Từ xuất hiện nhiều trong một recipe nhưng không quá phổ biến trong toàn bộ dataset sẽ có trọng số cao hơn.

Quy trình:

1. Lấy text nguyên liệu của mỗi recipe.
2. Tạo ma trận TF-IDF với unigram/bigram và giới hạn feature.
3. Biến query nguyên liệu của người dùng thành vector cùng không gian.
4. Tính Cosine Similarity giữa query và từng recipe.
5. Sắp xếp giảm dần để trả về các recipe gần nhất.

Ý nghĩa môn học:

- Đây là ví dụ chuyển dữ liệu text bán cấu trúc thành feature định lượng.
- Kết quả phụ thuộc trực tiếp vào bước cleaning nguyên liệu.
- Mô hình dễ tái lập, dễ giải thích và phù hợp làm baseline.

Hạn chế:

- Không hiểu đồng nghĩa như `aubergine` và `eggplant`.
- Không sửa lỗi chính tả.
- Nguyên liệu bị cleaning sai sẽ làm vector sai.

## 4. Mô hình phân loại

Project xem mỗi nhãn ăn kiêng là một bài toán nhị phân:

- Vegetarian hoặc không Vegetarian.
- Vegan hoặc không Vegan.
- Gluten-free hoặc không Gluten-free.

Feature đầu vào là `raw_ingredients`, không dùng title/description để giảm rủi ro mô hình học trực tiếp từ chữ trong tên món.

### Naive Bayes

Multinomial Naive Bayes phù hợp với dữ liệu đếm từ. Mô hình nhanh, đơn giản, dễ giải thích và thường là baseline tốt cho text classification.

Hạn chế: giả định các từ độc lập có điều kiện theo class, nên không nắm tốt quan hệ ngữ cảnh giữa các từ.

### Logistic Regression

Logistic Regression học trọng số cho từng feature để dự đoán xác suất thuộc class positive.

Ưu điểm: thường mạnh hơn Naive Bayes trên dữ liệu text đã vector hóa, đặc biệt khi có đủ mẫu. Trong dataset này, Logistic Regression cho F1 cao hơn ở cả Vegetarian, Vegan và Gluten-free.

Hạn chế: với lớp mất cân bằng như Vegan, cần thêm class weight hoặc điều chỉnh threshold nếu muốn tăng recall.

## 5. Metrics cần đọc như thế nào

| Metric | Ý nghĩa | Cách diễn giải trong project |
|---|---|---|
| Accuracy | Tỷ lệ dự đoán đúng tổng thể | Dễ hiểu nhưng có thể đánh lừa khi lớp mất cân bằng. |
| Precision | Trong các mẫu dự đoán positive, bao nhiêu mẫu đúng | Cao nghĩa là ít gán nhầm label ăn kiêng. |
| Recall | Trong các mẫu positive thật, mô hình tìm được bao nhiêu | Quan trọng với Vegan vì positive ít và dễ bị bỏ sót. |
| F1 | Trung bình điều hòa giữa precision và recall | Dùng để so sánh cân bằng hơn accuracy. |
| Confusion Matrix | TN, FP, FN, TP | Giúp biết mô hình sai do gán nhầm hay bỏ sót. |
| Cross-validation | Đánh giá trên nhiều fold | Giảm phụ thuộc vào một train/test split duy nhất. |

Ví dụ quan trọng: Vegan Logistic Regression có accuracy 0.9130 nhưng recall chỉ 0.2800. Nghĩa là mô hình đúng nhiều vì phần lớn recipe không Vegan, nhưng vẫn bỏ sót nhiều recipe Vegan thật.

## 6. Vấn đề dữ liệu ảnh hưởng đến mô hình

1. Dietary labels là nhãn lấy từ website, có thể thiếu hoặc không nhất quán.
2. Vegan có 123 positive trên 1146 recipes, gây mất cân bằng.
3. Cleaning nguyên liệu còn lỗi regex như mất chữ đầu ở một số nguyên liệu.
4. Các nhãn có thể chồng nhau vì đây là multi-label data.
5. Không có ground truth được gán nhãn thủ công độc lập.

## 7. Kết luận cho báo cáo môn học

Các mô hình hiện tại phù hợp vai trò baseline:

- TF-IDF search chứng minh được quy trình biến text nguyên liệu thành vector và tìm kiếm theo độ tương đồng.
- Naive Bayes và Logistic Regression cho phép so sánh hai thuật toán phổ biến trên cùng feature text.
- Logistic Regression là lựa chọn tốt hơn trên dataset hiện tại theo F1.
- Cần nhấn mạnh hạn chế class imbalance và noisy labels khi trình bày kết quả, đặc biệt với Vegan.
