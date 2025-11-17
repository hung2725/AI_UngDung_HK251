# train_model.py (ĐÃ SỬA LOGIC ĐẾM LƯỢT NGHE)
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import joblib
import time
import sys
import os
import random # Thêm thư viện random cho logic 3-sao

print("Bắt đầu quá trình 'huấn luyện' (tính toán ma trận + thống kê)...")
start_time = time.time()

# --- 1. ĐỊNH NGHĨA TÊN FILE ---
FEEDBACK_FILE = "user_feedback.csv"
SONGS_FILE = "vpop_songs_5000.csv"
OUTPUT_MATRIX_FILE = "similarity_matrix.joblib"
OUTPUT_STATS_FILE = "song_stats.csv"

# --- 2. TẢI DỮ LIỆU ---
try:
    print("...Đang tải file feedback (có thể mất vài giây)...")
    
    # Sử dụng 'low_memory=False' để tắt DtypeWarning một cách an toàn
    feedback_df = pd.read_csv(FEEDBACK_FILE, low_memory=False)
    
    feedback_df.rename(columns={"user id": "user_id", "song id": "song_id"}, inplace=True)

    print("...Đang dọn dẹp dữ liệu rác...")
    original_count = len(feedback_df)
    
    # Chuyển đổi an toàn các cột số, biến rác thành NaN
    numeric_cols = ['song_id', 'like', 'play_count', 'rating']
    for col in numeric_cols:
        feedback_df[col] = pd.to_numeric(feedback_df[col], errors='coerce')
        
    # Xóa các dòng có song_id hoặc user_id bị hỏng
    feedback_df.dropna(subset=['song_id', 'user_id'], inplace=True)
    cleaned_count = len(feedback_df)
    print(f"...Đã loại bỏ {original_count - cleaned_count} dòng dữ liệu hỏng.")

    # Ép kiểu dữ liệu sau khi đã dọn dẹp
    feedback_df = feedback_df.astype({
        'song_id': 'int64',
        'like': 'int8',
        'play_count': 'int16',
        'rating': 'int8',
        'user_id': 'str'
    })

    print("...Đang tải file bài hát...")
    songs_df = pd.read_csv(SONGS_FILE)
    if "id" in songs_df.columns:
        songs_df.rename(columns={"id": "song_id"}, inplace=True)
    
    # FIX LỖI LINK VIDEO
    songs_df.fillna("", inplace=True)
    
except Exception as e:
    print(f"LỖI TẢI DỮ LIỆU: {e}")
    sys.exit()

# --- 3. TẠO MA TRẬN TƯƠNG ĐỒNG ---
print("...Đang tạo ma trận tương đồng...")
try:
    user_song_matrix = feedback_df.pivot_table(
        index="song_id",
        columns="user_id",
        values="rating",
        fill_value=0
    )
    if not user_song_matrix.empty:
        similarity_matrix = cosine_similarity(user_song_matrix)
        sim_df = pd.DataFrame(
            similarity_matrix,
            index=user_song_matrix.index,
            columns=user_song_matrix.index
        )
        joblib.dump(sim_df, OUTPUT_MATRIX_FILE)
        print(f"...Đã lưu: {OUTPUT_MATRIX_FILE}")
    else:
        print("CẢNH BÁO: Không có dữ liệu rating để tạo ma trận.")
except Exception as e:
    print(f"LỖI khi tạo ma trận: {e}")
    
# --- 4. TẠO FILE THỐNG KÊ (CHO WEB) ---
print("...Đang tính toán thống kê (Lượt nghe, Rating, Like)...")
try:
    # *** SỬA LỖI LOGIC: ĐẾM (count) thay vì TỔNG (sum) ***
    # Dòng code cũ: play_counts = feedback_df.groupby('song_id')['play_count'].sum().reset_index()
    # Dòng code mới (đếm số lần xuất hiện của song_id, đây mới là lượt nghe thực tế):
    play_counts = feedback_df.groupby('song_id').size().reset_index(name='play_count')
    print("...Đã tính lượt nghe (play_count) bằng cách đếm số dòng.")
    
    # Đánh giá sao
    valid_ratings_df = feedback_df[feedback_df['rating'] > 0]
    avg_ratings = valid_ratings_df.groupby('song_id')['rating'].agg(['mean', 'count']).reset_index()
    avg_ratings.rename(columns={'mean': 'avg_rating', 'count': 'rating_count'}, inplace=True)
    
    # Logic Like/Dislike (3 sao = 50/50 Random)
    def categorize_rating_random(rating):
        if rating <= 2: return (0, 1) # (like, dislike)
        elif rating >= 4: return (1, 0)
        elif rating == 3:
            return (1, 0) if random.random() < 0.5 else (0, 1)
        return (0, 0)

    feedback_df[['inferred_like', 'inferred_dislike']] = pd.DataFrame(
        feedback_df['rating'].apply(categorize_rating_random).tolist(), 
        index=feedback_df.index
    )
    
    likes_dislikes = feedback_df.groupby('song_id').agg(
        likes=('inferred_like', 'sum'),
        dislikes=('inferred_dislike', 'sum')
    ).reset_index()

    # Gộp tất cả lại
    stats_df = songs_df.merge(play_counts, on='song_id', how='left')
    stats_df = stats_df.merge(avg_ratings, on='song_id', how='left')
    stats_df = stats_df.merge(likes_dislikes, on='song_id', how='left')
    
    # Dọn dẹp
    stats_df.fillna({
        'play_count': 0, 'avg_rating': 0, 'rating_count': 0,
        'likes': 0, 'dislikes': 0
    }, inplace=True)
    
    # Điền "" cho các cột TEXT
    stats_df.fillna("", inplace=True)
    
    # Lưu file
    stats_df.to_csv(OUTPUT_STATS_FILE, index=False)
    print(f"...Đã lưu: {OUTPUT_STATS_FILE}")

except Exception as e:
    print(f"LỖI khi tính toán thống kê: {e}")
    sys.exit()

# --- 5. HOÀN TẤT ---
end_time = time.time()
print(f"--- HOÀN TẤT! ({end_time - start_time:.2f} giây) ---")