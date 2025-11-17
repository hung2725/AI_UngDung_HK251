import pandas as pd
import numpy as np
import joblib

class VPopRecommender:
    def __init__(self, songs_file, matrix_file):
        """
        Recommender IBCF Hệ khuyến Nghị:
        Tải ma trận tương đồng đã được tính toán.
        songs_file: CSV bài hát (vpop_songs_5000.csv)
        matrix_file: File ma trận đã huấn luyện 
        """
        # load dữ liệu bài hát
        try:
            self.songs_df = pd.read_csv(songs_file)
            self.songs_df.fillna("", inplace=True)
            if "id" in self.songs_df.columns: # Đổi cột 'id' file từ vpop_songs_5000 thành 'song_id' để khớp
                self.songs_df.rename(columns={"id": "song_id"}, inplace=True)
        except FileNotFoundError:
            print(f"LỖI (Recommender): Không tìm thấy file bài hát: {songs_file}")
            self.songs_df = pd.DataFrame() # Khởi tạo rỗng để tránh lỗi

        #load ma trận tương đồng đã được huấn luyện
        try:
            self.similarity_matrix = joblib.load(matrix_file)
        except FileNotFoundError:
            print(f"LỖI (Recommender): Không tìm thấy file ma trận: {matrix_file}")
            print("Vui lòng chạy file 'train_model.py' trước để tạo file này.")
            self.similarity_matrix = pd.DataFrame() # Khởi tạo rỗng
    
    def recommend(self, song_name, artist, top_n=5):#hmaf gợi ý
        if self.songs_df.empty or self.similarity_matrix.empty:
            return [] # Trả về rỗng nếu dữ liệu chưa được load
        #lấy song_id từ song_name + artist
        match = self.songs_df[
            (self.songs_df["name"].str.lower() == song_name.lower()) &
            (self.songs_df["artist"].str.lower() == artist.lower())
        ]
        if match.empty:
            return []
        
        song_id = match.iloc[0]["song_id"]
        
        if song_id not in self.similarity_matrix.index:
            return [] # Bài hát chưa có trong ma trận (chưa ai rate)
        
        # Lấy similarity của bài đó với tất cả bài khác
        sims = self.similarity_matrix[song_id].drop(song_id)
        top_songs = sims.sort_values(ascending=False).head(top_n)
        
        # Trả về danh sách bài hát
        results = []
        for sid in top_songs.index:
            if top_songs[sid] > 0.0: # Chỉ gợi ý nếu độ tương đồng > 0
                song_info_match = self.songs_df[self.songs_df["song_id"] == sid]
                if not song_info_match.empty:
                    song_info = song_info_match.iloc[0]
                    results.append({
                        "song_id": song_info["song_id"], 
                        "name": song_info["name"],
                        "artist": song_info["artist"],
                        "album": song_info.get("album", ""),
                        "image": song_info.get("image", ""),
                        "youtube_url": song_info.get("youtube_url", ""),
                        "similarity": float(top_songs[sid])
                    })
        return results