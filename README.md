## V-POP Recommender Dashboard

Ứng dụng quản trị V-POP cung cấp hệ thống gợi ý nhạc item-based tối ưu hóa và giao diện Streamlit để khám phá, phân tích, quản lý danh sách yêu thích.

---

## Thành phần chính

- `train_model.py`: Tính toán ma trận tương đồng item-item từ dữ liệu phản hồi và lưu thành `similarity_matrix.joblib`.
- `recommender.py`: Lớp `VPopRecommender` tải danh sách bài hát và ma trận tương đồng đã huấn luyện để trả về danh sách gợi ý.
- `app.py`: Dashboard Streamlit phục vụ khám phá, xem gợi ý, thống kê và quản lý danh sách yêu thích (lưu vào SQLite).

---

## Yêu cầu hệ thống

- Python >= 3.9 (khuyến nghị 3.10/3.11).
- Pip đã cài đặt.

Khuyến nghị tạo môi trường ảo:

```powershell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
```

---

## Cài đặt phụ thuộc

Trong thư mục dự án:

```powershell
pip install -r requirements.txt
```

Các package quan trọng: `streamlit`, `pandas`, `numpy`, `scikit-learn`, `joblib`. `sentence-transformers` có trong requirements nhưng hiện chưa bắt buộc cho pipeline gợi ý.

---

## Chuẩn bị dữ liệu

### `vpop_songs_5000.csv`
- Chứa metadata hiển thị trên UI.
- Cột tối thiểu: `name`, `artist`. Nên có thêm `song_id`, `album`, `image`, `youtube_url`.
- Nếu file dùng cột `id`, `VPopRecommender` sẽ tự đổi thành `song_id`. Đảm bảo `song_id` là duy nhất.

Ví dụ:

```csv
song_id,name,artist,image,youtube_url
123,Bài hát A,Nghệ sĩ A,https://...jpg,https://www.youtube.com/watch?v=...
456,Bài hát B,Nghệ sĩ B,https://...jpg,https://www.youtube.com/watch?v=...
```

### `user_feedback.csv`
- Dữ liệu tín hiệu người dùng để huấn luyện ma trận tương đồng.
- Cột mong đợi: `user_id`, `song_id`, `rating`. Nếu thiếu `rating` nhưng có `like`, script sẽ map tự động (`like=1 -> rating=5`, `like=0 -> rating=1`).
- Cột khuyến nghị: `play_count`, `like`. Ứng dụng dùng để thống kê lượt nghe, suy luận lượt thích/không thích.
- Các cột `user id`, `song id` sẽ tự đổi tên về chuẩn snake_case.

Ví dụ:

```csv
user_id,song_id,rating,play_count
u1,123,5,34
u1,456,1,5
u2,123,4,20
```

> **Lưu ý:** `song_id` trong cả hai file phải khớp để gợi ý và thống kê hoạt động chính xác.

---

## Huấn luyện ma trận tương đồng

1. Kiểm tra `user_feedback.csv` hợp lệ.
2. Chạy:

```powershell
python train_model.py
```

Quy trình:
- Đổi tên các cột sai chuẩn, điền giá trị khuyết (`fillna(0)`).
- Pivot dữ liệu thành ma trận bài hát × người dùng.
- Tính cosine similarity, chuyển thành DataFrame có index/column là `song_id`.
- Lưu file `similarity_matrix.joblib` để tái sử dụng nhanh trong ứng dụng.

Nếu thiếu cột hoặc ma trận rỗng, script sẽ thông báo chi tiết và dừng chạy.

---

## Sử dụng `VPopRecommender`

```python
from recommender import VPopRecommender

reco = VPopRecommender("vpop_songs_5000.csv", "similarity_matrix.joblib")
results = reco.recommend(song_name="Bài hát A", artist="Nghệ sĩ A", top_n=5)

for item in results:
    print(item["name"], "-", item["artist"], f"{item['similarity']:.2f}")
```

- Lớp tự tải CSV bài hát, đổi tên `id` → `song_id` nếu cần và lưu vào `self.songs_df`.
- Ma trận tương đồng được nạp bằng `joblib.load`.
- Phương thức `recommend` tìm `song_id` theo cặp `name` + `artist` (không phân biệt hoa thường) và trả về danh sách bài hát với metadata (`album`, `image`, `youtube_url`, `similarity`).
- Chỉ trả về bài có độ tương đồng > 0 nhằm loại bỏ gợi ý kém liên quan.

---

## Chạy ứng dụng Streamlit

```powershell
streamlit run app.py
```

### Trang “Khám phá”
- Chọn và phát bài hát (ảnh, video YouTube nếu có).
- Hiển thị thống kê lượt nghe, lượt thích/không thích, điểm trung bình rating.
- Gợi ý “Có thể bạn sẽ thích” dựa trên ma trận đã huấn luyện, kèm thanh tiến trình độ tương đồng.
- Thêm bài vào danh sách yêu thích cá nhân (lưu vào SQLite).

### Trang “Yêu thích”
- Lưu trữ danh sách yêu thích trong `favorites.db`.
- Có nút phát nhanh, xóa từng bài hoặc xóa toàn bộ danh sách.

### Trang “Bảng xếp hạng”
- Ba tab cho Top theo đánh giá sao, lượt nghe, lượt thích.
- Dữ liệu tổng hợp từ `user_feedback.csv` (play_count, rating trung bình, likes/dislikes).

### Lưu ý triển khai
- `@st.cache_data` giúp cache dữ liệu; cần “Rerun” hoặc clear cache khi cập nhật CSV.
- Các nút sử dụng `width='stretch'` để tương thích với API mới của Streamlit.
- `favorites.db` tự sinh khi chạy lần đầu; không cần tạo thủ công.

---

## Kiến trúc dữ liệu & xử lý

- `load_data()` trong `app.py`:
  - Tải `vpop_songs_5000.csv` và chuẩn hóa `song_id`.
  - Tải `user_feedback.csv`, chuẩn hóa tên cột, tính tổng `play_count`, trung bình & số lượt rating.
  - Suy luận likes/dislikes từ `rating` (`>=4` xem là thích, `<=2` xem là không thích`).
  - Gộp tất cả vào `stats_df` để dùng cho thống kê và bảng xếp hạng.
- `VPopRecommender` được khởi tạo một lần khi app chạy để tránh tính toán lặp lại.

---

## Lỗi thường gặp

- **Không có gợi ý**: Bài hát chưa có trong ma trận (thiếu phản hồi), hoặc `song_name`/`artist` không khớp chính xác. Cần bổ sung feedback và chạy lại `train_model.py`.
- **Video không hiển thị**: Thiếu `youtube_url` hoặc link sai định dạng.
- **CSV lỗi**: Kiểm tra encoding UTF-8, ký tự phân tách, hoặc đường dẫn file.
- **Cài đặt package thất bại**: Nên nâng cấp pip (`python -m pip install --upgrade pip`) và cài đặt Visual C++ Build Tools nếu cần.

---

## Cấu trúc thư mục (rút gọn)

```
DM01/
├─ app.py
├─ recommender.py
├─ train_model.py
├─ requirements.txt
├─ vpop_songs_5000.csv
├─ user_feedback.csv
├─ similarity_matrix.joblib     # tạo sau khi huấn luyện
├─ favorites.db                 # tạo khi chạy app
└─ Logo.png
```

---

## Quy trình khởi chạy nhanh

```powershell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python train_model.py  # nếu chưa có similarity_matrix.joblib
streamlit run app.py
```





