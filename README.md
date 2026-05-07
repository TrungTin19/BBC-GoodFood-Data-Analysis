# 🍳 Thu thập và Phân loại Công thức Nấu ăn Thông minh từ BBC Good Food

> **Đồ án môn học:** Kỹ thuật lập trình trong Phân tích dữ liệu  
> **Giảng viên:** Trịnh Trọng Thành  
> **Trường:** Đại học Thủ Dầu Một – Viện Công nghệ số

---

## 📋 Mô tả dự án

Dự án xây dựng hệ thống **thu thập, làm sạch, lưu trữ và tìm kiếm thông minh** công thức nấu ăn từ [BBC Good Food](https://www.bbcgoodfood.com/recipes/). Kết hợp kỹ thuật **web scraping**, **cơ sở dữ liệu SQLite**, **TF-IDF + Cosine Similarity** để tìm kiếm theo nguyên liệu, và **Naive Bayes** để phân loại chế độ ăn tự động.

### Tính năng chính

- 🕷️ **Crawl** 1000+ công thức từ BBC Good Food qua **Sitemap XML** và **Collection pages** (tuân thủ `robots.txt`)
- 🧹 **Làm sạch** nguyên liệu: loại bỏ số lượng, đơn vị, hướng dẫn chế biến
- 📖 **Trích xuất** đầy đủ công thức nấu (instructions) từ JSON-LD và HTML
- 💾 **Lưu trữ** vào SQLite với 2 bảng `recipes` + `ingredients` (khóa ngoại, chống trùng)
- 🔍 **Tìm kiếm thông minh** bằng TF-IDF + Cosine Similarity theo nguyên liệu người dùng nhập
- 🔤 **Tìm kiếm theo tên** món ăn (partial match, case-insensitive)
- 🤖 **Phân loại chế độ ăn** (Vegetarian, Vegan, Gluten-free) bằng Multinomial Naive Bayes
- 📊 **Biểu đồ thống kê** (phân bố độ khó, rating, top nguyên liệu, thời gian nấu, chế độ ăn)
- 🖥️ **Giao diện web Streamlit** để tìm kiếm và khám phá công thức

---

## 🗂️ Cấu trúc dự án

```
Do_An/
├── config.py           # Cấu hình chung (URL, delay, DB path, ML params)
├── crawler.py          # Thu thập URL công thức (Sitemap XML + Collection pages)
├── parser.py           # Trích xuất & làm sạch dữ liệu từ HTML/JSON-LD
├── database.py         # Quản lý SQLite (tạo bảng, CRUD, thống kê)
├── ml_search.py        # TF-IDF search engine + Naive Bayes classifiers
├── visualize.py        # Tạo biểu đồ matplotlib/seaborn
├── app.py              # Giao diện Streamlit
├── main.py             # Script điều phối chính (7 phases)
├── requirements.txt    # Thư viện cần cài đặt
├── Tai_Lieu.md         # Tài liệu tham khảo
├── data/               # (tự tạo) Chứa recipes.db và models/
├── charts/             # (tự tạo) Chứa biểu đồ PNG
└── logs/               # (tự tạo) Chứa file log
```

---

## ⚙️ Cài đặt

### Yêu cầu hệ thống

- Python 3.9+
- Kết nối Internet (để crawl dữ liệu)

### Cài đặt thư viện

```bash
pip install -r requirements.txt
```

Các thư viện chính:

| Thư viện | Mục đích |
|----------|----------|
| `requests` | Gửi HTTP request |
| `beautifulsoup4` | Parse HTML |
| `lxml` | Parse XML (sitemap) |
| `pandas` | Xử lý dữ liệu |
| `scikit-learn` | TF-IDF, Naive Bayes, đánh giá mô hình |
| `matplotlib` / `seaborn` | Trực quan hóa |
| `streamlit` | Giao diện web |
| `sqlite3` | Cơ sở dữ liệu (built-in) |

---

## 🚀 Hướng dẫn sử dụng

### 1. Chạy toàn bộ pipeline

```bash
python main.py
```

Pipeline thực hiện 7 bước tự động:

| Phase | Mô tả |
|-------|-------|
| 1 | Khởi tạo database SQLite |
| 2 | Kiểm tra `robots.txt` (xác nhận quyền crawl) |
| 3 | Thu thập URL công thức từ Sitemap XML + Collection pages |
| 4 | Parse dữ liệu chi tiết từng công thức (JSON-LD + HTML) |
| 5 | Lưu vào database (batch, chống trùng) |
| 6 | Huấn luyện mô hình ML (Naive Bayes) |
| 7 | Tạo biểu đồ thống kê |

### 2. Tùy chọn dòng lệnh

```bash
# Bỏ qua crawl (dùng dữ liệu đã có)
python main.py --skip-crawl

# Bỏ qua huấn luyện ML
python main.py --skip-ml

# Bỏ qua tạo biểu đồ
python main.py --skip-charts
```

### 3. Chạy giao diện Streamlit

```bash
streamlit run app.py
```

Giao diện gồm 3 tab:
- **🔎 Tìm kiếm**: Tìm theo **tên món ăn** hoặc **nguyên liệu**, lọc theo rating và chế độ ăn, xem nguyên liệu và công thức nấu trực tiếp
- **📊 Thống kê**: Xem số liệu tổng hợp và biểu đồ
- **🤖 ML Classification**: Dự đoán chế độ ăn từ nguyên liệu

---

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────┐
│                    main.py                          │
│              (Điều phối pipeline)                   │
├──────────┬──────────┬──────────┬────────────────────┤
│          │          │          │                    │
│ crawler  │ parser   │ database │  ml_search         │
│   .py    │   .py    │   .py    │    .py             │
│          │          │          │                    │
│ Sitemap  │ Trích    │ SQLite   │ TF-IDF Search      │
│ XML +    │ xuất &   │ recipes  │ + Naive Bayes      │
│ Collecti │ làm sạch │ + ingre- │ Classification     │
│ on pages │ JSON-LD  │ dients   │                    │
├──────────┴──────────┴──────────┴────────────────────┤
│                                                     │
│  visualize.py          app.py (Streamlit)           │
│  Biểu đồ thống kê     Giao diện web tương tác      │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 🗄️ Thiết kế Database

### Bảng `recipes`

| Trường | Kiểu | Ràng buộc | Mô tả |
|--------|------|-----------|-------|
| `recipe_id` | INTEGER | PRIMARY KEY | Mã công thức (tự tăng) |
| `title` | TEXT | NOT NULL | Tên món ăn |
| `url` | TEXT | UNIQUE NOT NULL | Đường dẫn gốc |
| `prep_time_min` | INTEGER | | Thời gian chuẩn bị (phút) |
| `cook_time_min` | INTEGER | | Thời gian nấu (phút) |
| `difficulty` | TEXT | | Độ khó (Easy / More effort / A challenge) |
| `rating` | REAL | | Điểm đánh giá (0-5) |
| `review_count` | INTEGER | DEFAULT 0 | Số lượt đánh giá |
| `dietary_labels` | TEXT | | Nhãn chế độ ăn (phân cách bằng dấu phẩy) |
| `raw_ingredients` | TEXT | | Nguyên liệu thô (dùng cho ML) |
| `instructions` | TEXT | | Các bước nấu ăn chi tiết |

### Bảng `ingredients`

| Trường | Kiểu | Ràng buộc | Mô tả |
|--------|------|-----------|-------|
| `id` | INTEGER | PRIMARY KEY | ID tự tăng |
| `recipe_id` | INTEGER | FOREIGN KEY → recipes | Mã công thức |
| `ingredient` | TEXT | NOT NULL | Tên nguyên liệu đã làm sạch |

> Ràng buộc: `ON DELETE CASCADE` — xóa công thức sẽ tự động xóa nguyên liệu liên quan.

---

## 🕷️ Chiến lược Thu thập Dữ liệu

Hệ thống sử dụng **2 phương pháp** thu thập URL bổ trợ lẫn nhau:

1. **Sitemap XML** (nguồn chính):
   - Đọc `sitemap.xml` → tìm các quarterly recipe sitemaps (`YYYY-QN-recipe.xml`)
   - Parse từng sitemap → lấy URL dạng `/recipes/slug`
   - Lọc bỏ URL premium, collection, category

2. **Collection Pages** (nguồn bổ sung):
   - Crawl trang `/recipes/` → tìm các link `/recipes/collection/`
   - Parse từng collection → lấy thêm URL công thức
   - Chỉ kích hoạt nếu sitemap chưa đủ 1000 URL

**Tuân thủ**: `robots.txt`, `Crawl-delay: 1s`, retry tối đa 3 lần, bỏ qua URL đã crawl.

---

## 🔬 Kỹ thuật Machine Learning

### TF-IDF + Cosine Similarity (Tìm kiếm)

1. Nối tất cả nguyên liệu sạch của mỗi công thức thành chuỗi
2. Xây dựng ma trận TF-IDF (`stop_words='english'`, `ngram_range=(1,2)`, `max_features=5000`)
3. Biến đổi query của người dùng thành vector TF-IDF
4. Tính Cosine Similarity → sắp xếp giảm dần → trả về top N kết quả

### Naive Bayes (Phân loại chế độ ăn)

- **Input**: `raw_ingredients` (văn bản nguyên liệu thô)
- **Labels**: nhãn nhị phân (`is_vegetarian`, `is_vegan`, `is_gluten_free`)
- **Pipeline**: `CountVectorizer` → `MultinomialNB`
- **Chia dữ liệu**: 80% train / 20% test (stratified)
- **Đánh giá**: Accuracy, Precision, Recall, F1-Score, Confusion Matrix

---

## 📊 Biểu đồ thống kê

Sau khi chạy pipeline, các biểu đồ được lưu trong thư mục `charts/`:

| File | Nội dung |
|------|----------|
| `difficulty_distribution.png` | Phân bố độ khó |
| `rating_distribution.png` | Phân bố rating (histogram + KDE) |
| `top_ingredients.png` | Top 10 nguyên liệu phổ biến nhất |
| `time_distribution.png` | Phân bố thời gian prep/cook |
| `dietary_labels.png` | Phân bố nhãn chế độ ăn |

---

## ⚠️ Lưu ý

- **Thời gian crawl**: Khoảng 30-50 phút cho 1000+ công thức (do tuân thủ `Crawl-delay: 1s`)
- **Tuân thủ robots.txt**: Chương trình tự động kiểm tra quyền crawl trước khi bắt đầu
- **Resume crawl**: Nếu bị gián đoạn, chạy lại `python main.py` — chương trình sẽ bỏ qua URL đã lưu
- **Cấu trúc HTML**: BBC Good Food có thể thay đổi giao diện, cần cập nhật selectors trong `parser.py`

---

## 📚 Tài liệu tham khảo

1. BBC Good Food – `robots.txt`: https://www.bbcgoodfood.com/robots.txt
2. BeautifulSoup Documentation: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
3. Scikit-learn – Machine Learning in Python: https://scikit-learn.org/
4. Streamlit Documentation: https://docs.streamlit.io/
5. Python SQLite3: https://docs.python.org/3/library/sqlite3.html

---

## 👥 Nhóm thực hiện

| Thành viên | Nhiệm vụ |
|------------|----------|
| A | Crawl danh sách & phân trang, kiểm soát trùng lặp URL |
| B | Parse trang chi tiết, làm sạch nguyên liệu, chuyển đổi thời gian |
| C | Thiết kế CSDL, TF-IDF search, Naive Bayes, giao diện Streamlit |
| Cả nhóm | Viết báo cáo, thiết kế slide, thuyết trình |
