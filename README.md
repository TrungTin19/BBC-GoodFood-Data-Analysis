# 🍳 Thu thập và Phân loại Công thức Nấu ăn Thông minh từ BBC Good Food

> **Đồ án môn học:** Kỹ thuật lập trình trong Phân tích dữ liệu  
> **Giảng viên:** Trịnh Trọng Thành  
> **Trường:** Đại học Thủ Dầu Một – Viện Công nghệ số

---

## 📋 Mô tả dự án

Dự án xây dựng hệ thống **thu thập, làm sạch, lưu trữ và tìm kiếm thông minh** công thức nấu ăn từ [BBC Good Food](https://www.bbcgoodfood.com/recipes/). Kết hợp kỹ thuật **web scraping**, **cơ sở dữ liệu SQLite**, **TF-IDF + Cosine Similarity** để tìm kiếm theo nguyên liệu, và **Naive Bayes** để phân loại chế độ ăn tự động.

### Tính năng chính

- 🕷️ **Crawl** 1000+ công thức từ BBC Good Food qua **Sitemap XML** và **Collection pages** (tuân thủ `robots.txt`, hỗ trợ resume)
- 🧹 **Làm sạch** nguyên liệu: loại bỏ số lượng, đơn vị, hướng dẫn chế biến bằng Regex chuyên sâu
- 📖 **Trích xuất** đầy đủ công thức nấu (instructions) từ JSON-LD và HTML fallback
- 💾 **Lưu trữ** vào SQLite (Normalized, WAL mode, Parameterized Queries chống SQL Injection)
- 🔍 **Tìm kiếm thông minh** bằng TF-IDF + Cosine Similarity theo nguyên liệu
- 🔤 **Tìm kiếm theo tên** món ăn (Partial match, Theme-aware UI)
- 🤖 **Phân loại chế độ ăn** (Vegetarian, Vegan, Gluten-free) bằng **Naive Bayes** & **Logistic Regression**
- 🧪 **Đánh giá mô hình**: Sử dụng **5-Fold Cross-Validation** để đảm bảo độ ổn định
- 🌐 **REST API**: Cung cấp các endpoint Flask (hỗ trợ CORS) để tích hợp hệ thống khác
- 📊 **Biểu đồ thống kê**: Trực quan hóa dữ liệu bằng Matplotlib/Seaborn
- 🖥️ **Giao diện Premium**: UI Streamlit hiện đại, tự động thích ứng Light/Dark mode, layout Flexbox chuẩn xác

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
├── app.py              # Giao diện Streamlit (Premium UI)
├── api.py              # REST API Flask (CORS enabled)
├── main.py             # Script điều phối chính (7 phases)
├── requirements.txt    # Thư viện cần cài đặt (Flask-CORS, etc.)
├── .gitignore          # Cấu hình bỏ qua file model (.pkl) và data/
├── data/               # Chứa recipes.db và models/ (đã được ignore)
├── charts/             # Chứa biểu đồ PNG tự động tạo
└── logs/               # Log quá trình crawl và training
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

### Naive Bayes & Logistic Regression (Phân loại chế độ ăn)

- **Input**: `raw_ingredients` (văn bản nguyên liệu thô)
- **Labels**: Nhãn nhị phân cho từng loại chế độ ăn.
- **Mô hình**:
    - **Multinomial Naive Bayes**: Nhanh, hiệu quả với dữ liệu văn bản.
    - **Logistic Regression**: Trọng số tối ưu, capture tương quan tốt hơn.
- **Đánh giá nâng cao**:
    - **5-Fold Cross-Validation**: Đánh giá độ ổn định trên toàn bộ tập dữ liệu.
    - **Metrics**: Accuracy, Precision, Recall, F1-Score, Confusion Matrix.
- **Lưu trữ**: Model được đóng gói dạng `.pkl` để tái sử dụng nhanh.

### REST API (Flask)

Dự án cung cấp hệ thống API mạnh mẽ tại cổng `5000`:
- `GET /api/stats`: Thống kê tổng quan.
- `GET /api/recipes`: Danh sách món ăn (Phân trang SQL).
- `GET /api/search?q=...`: Tìm kiếm TF-IDF.
- **Bảo mật**: Hỗ trợ **CORS** cho phép các ứng dụng Frontend khác truy cập.

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
| **Crawl & Data** | Thu thập 1000+ URL (Sitemap/Collection), xử lý Session reuse, Exponential backoff. |
| **Parser & Cleaning** | Trích xuất JSON-LD, làm sạch nguyên liệu bằng Regex, xử lý ISO 8601 duration. |
| **Backend & ML** | Thiết kế CSDL (WAL mode), TF-IDF Search, Naive Bayes & Logistic Regression, 5-Fold Cross-Validation. |
| **API & Security** | Phát triển Flask API, tích hợp CORS, Parameterized Queries bảo mật. |
| **Frontend UI** | Giao diện Streamlit Premium, Theme-aware (Light/Dark), Flexbox layout, Visualize data. |
| **Cả nhóm** | Kiểm thử (Test Suite), Viết báo cáo, thuyết trình. |
