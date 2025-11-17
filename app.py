# app.py

import streamlit as st
import pandas as pd
import sqlite3
import random
from recommender import VPopRecommender
import os
import csv 
import time
from datetime import datetime
import altair as alt # Thư viện vẽ biểu đồ

# 1. CẤU HÌNH & CSS 
st.set_page_config(page_title="V-POP AI Music", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;700;800&display=swap');

    /* --- GLOBAL --- */
    body, .main, .stApp {
        font-family: 'Montserrat', sans-serif !important;
        background-color: #000000 !important;
        color: #FFFFFF !important;
    }
    
    /* --- SIDEBAR --- */
    section[data-testid="stSidebar"] {
        background-color: #121212 !important;
        border-right: 1px solid #333;
    }
    
    /* --- MENU RADIO --- */
    .stRadio [role="radiogroup"] > label > div:first-child { display: none; }
    .stRadio [role="radiogroup"] > label {
        display: block; padding: 12px 20px; background-color: #121212;
        border-radius: 8px; margin-bottom: 10px; transition: all 0.2s;
        border: 1px solid #333; font-weight: 600; color: #B3B3B3;
    }
    .stRadio [role="radiogroup"] > label:hover {
        background-color: #282828; border-color: #1DB954; color: white; cursor: pointer;
    }
    .stRadio [role="radiogroup"] > div:has(input:checked) > label {
        background-color: #1DB954; color: #FFFFFF !important; border-color: #1DB954;
    }

    /* --- PLAYER HERO SECTION (INFO DƯỚI ẢNH) --- */
    .hero-container {
        background: #181818;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #333;
        text-align: center; /* Căn giữa nội dung */
        height: 100%;
    }
    
    /* Tên bài hát & Nghệ sĩ */
    .hero-title {
        font-size: 1.5rem; font-weight: 800; margin-top: 15px; margin-bottom: 5px; line-height: 1.2;
    }
    .hero-artist {
        font-size: 1rem; font-weight: 600; color: #1DB954; margin-bottom: 20px;
    }

    /* Grid Thống kê (3 cột) */
    .stats-row {
        display: flex; justify-content: space-around;
        background: #222; padding: 10px; border-radius: 8px;
        margin-top: 10px;
    }
    .stat-item { display: flex; flex-direction: column; }
    .stat-val { font-weight: 700; font-size: 1.1rem; color: white; }
    .stat-lbl { font-size: 0.7rem; color: #888; text-transform: uppercase; }

    /* --- SONG CARD (GỢI Ý) --- */
    .song-card {
        background-color: #181818; border-radius: 10px; padding: 15px;
        text-align: left; transition: all 0.3s; margin-bottom: 1rem;
        border: 1px solid #333;
        height: 100%;
    }
    .song-card:hover { transform: translateY(-5px); border-color: #1DB954; }
    .song-card img { border-radius: 8px; width: 100%; aspect-ratio: 1/1; object-fit: cover; margin-bottom: 10px; }

    /* --- KPI CARDS (Dashboard) --- */
    div[data-testid="stMetric"] {
        background-color: #181818; padding: 15px; border-radius: 10px; border: 1px solid #333; text-align: center;
    }
    div[data-testid="stMetric"] label { color: #888; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #1DB954; font-size: 1.8rem; }
    
    /* Căn giữa Feedback Stars */
    div[data-testid="stFeedback"] {
        justify-content: center;
    }
    </style>
""", unsafe_allow_html=True)

# 2. DATABASE & DATA LOADING
DB_FILE = "app_data.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cur = conn.cursor()

# Lưu vào Lịch sử
cur.execute("""CREATE TABLE IF NOT EXISTS favorites (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, song_id INTEGER, name TEXT, artist TEXT, image TEXT, youtube_url TEXT)""")
# Bảng History
cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        song_id INTEGER, name TEXT, artist TEXT, image TEXT,
        youtube_url TEXT, 
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.commit()

@st.cache_data
def load_data():
    SONGS_FILE = "vpop_songs_5000.csv"
    STATS_FILE = "song_stats.csv" 
    if not os.path.exists(SONGS_FILE) or not os.path.exists(STATS_FILE):
        return pd.DataFrame()
    try:
        stats_df = pd.read_csv(STATS_FILE)
        if "song_id" in stats_df.columns:
            stats_df.set_index("song_id", inplace=True)
        return stats_df
    except: return pd.DataFrame()

stats_df = load_data()

@st.cache_resource 
def load_recommender():
    if os.path.exists("similarity_matrix.joblib"):
        return VPopRecommender("vpop_songs_5000.csv", "similarity_matrix.joblib")
    return None

recommender = load_recommender()

# 3. LOGIC ĐĂNG NHẬP
if "user_info" not in st.session_state: st.session_state["user_info"] = None

def login_screen():
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("""
            <div style='text-align: center; background: #181818; padding: 40px; border-radius: 20px; border: 1px solid #333;'>
                <h1 style='color: #1DB954;'>V-POP AI</h1>
                <p style='color: #888;'>Trải nghiệm nghe nhạc thông minh</p>
            </div>
        """, unsafe_allow_html=True)
        username = st.text_input("Nhập tên của bạn:", placeholder="Ví dụ: son_tung_mtp")
        if st.button("Bắt đầu ngay", type="primary", use_container_width=True):
            if username:
                st.session_state["user_info"] = username
                if "favorites" in st.session_state:
                    del st.session_state["favorites"] # Xóa cache favs của user cũ
                st.rerun()

if st.session_state["user_info"] is None:
    login_screen()
    st.stop()

CURRENT_USER = st.session_state["user_info"]

# Load Favorites & State
favorites_df = pd.read_sql_query("SELECT song_id, name, artist, image, youtube_url FROM favorites WHERE user_id=?", conn, params=(CURRENT_USER,))
if "favorites" not in st.session_state: st.session_state["favorites"] = favorites_df.to_dict(orient="records")
if "current_song" not in st.session_state: st.session_state["current_song"] = None

# 4. CORE FUNCTIONS
def log_play_event(song):
    """Ghi Lịch sử (DB) và Lượt nghe (CSV)"""
    song_id = song.get('song_id')
    if not song_id or pd.isna(song_id):
        try:
            match = stats_df.reset_index()
            match = match[(match['name'] == song['name']) & (match['artist'] == song['artist'])]
            if not match.empty:
                song_id = match.iloc[0]['song_id']
        except: pass
            
    if not song_id or pd.isna(song_id):
        print(f"Không thể log play: Thiếu song_id cho {song['name']}")
        return 

    # 1. Lưu vào Lịch sử (SQLite DB)
    try:
        cur.execute("INSERT INTO history (user_id, song_id, name, artist, image, youtube_url) VALUES (?,?,?,?,?,?)",
                   (CURRENT_USER, song_id, song['name'], song['artist'], song.get('image',''), song.get('youtube_url','')))
        conn.commit()
    except Exception as e:
        print(f"Lỗi lưu history: {e}")

    # 2. Lưu +1 Lượt nghe vào user_feedback.csv
    feedback_file_path = "user_feedback.csv"
    new_row = {
        "user_id": CURRENT_USER, "song_id": song_id, 
        "like": 0, "play_count": 1, "rating": 0 
    }
    
    try:
        exists = os.path.exists(feedback_file_path)
        with open(feedback_file_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["user_id", "song_id", "like", "play_count", "rating"])
            if not exists: writer.writeheader()
            writer.writerow(new_row)
    except Exception as e:
        print(f"Lỗi lưu feedback (play): {e}")


def handle_rating():
    """Xử lý khi bấm sao (st.feedback)"""
    score = st.session_state.get("rating_input")
    song = st.session_state["current_song"]
    
    if score is not None and song:
        rating_value = score + 1
        is_like = 1 if rating_value >= 3 else 0
        
        feedback_file_path = "user_feedback.csv"
        new_row = {
            "user_id": CURRENT_USER, "song_id": song.get("song_id"), 
            "like": is_like, "play_count": 1, "rating": rating_value
        }
        try:
            exists = os.path.exists(feedback_file_path)
            with open(feedback_file_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=["user_id", "song_id", "like", "play_count", "rating"])
                if not exists: writer.writeheader()
                writer.writerow(new_row)
            st.toast(f"Đã đánh giá {rating_value} sao! ⭐")
        except: st.error("Lỗi lưu file")

# *** UI PLAYER (INFO DƯỚI ẢNH) ***
def play_song_ui(song, stats):
    
    c1, c2 = st.columns([1.2, 2], gap="large")
    
    # --- CỘT TRÁI: ẢNH + INFO + STATS (Thẳng hàng dọc) ---
    with c1:
        st.markdown("<div class='hero-container'>", unsafe_allow_html=True)
        
        st.image(song.get("image", "https://placehold.co/400"), use_container_width=True)
        
        st.markdown(f"<div class='hero-title'>{song['name']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='hero-artist'>{song['artist']}</div>", unsafe_allow_html=True)
        
        st.markdown(f"""
            <div class="stats-row">
                <div class="stat-item"><span class="stat-val">{int(stats.get('play_count', 0)):,}</span><span class="stat-lbl">Nghe</span></div>
                <div class="stat-item"><span class="stat-val">{stats.get('avg_rating', 0):.1f}/5</span><span class="stat-lbl">Rating</span></div>
                <div class="stat-item"><span class="stat-val">{int(stats.get('likes', 0)):,}</span><span class="stat-lbl">Like</span></div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("❤️ Thêm vào Yêu thích", use_container_width=True, key=f"fav_Main_{song.get('song_id')}"):
             if not any(f['name']==song['name'] for f in st.session_state["favorites"]):
                st.session_state["favorites"].append(song)
                cur.execute("INSERT INTO favorites (user_id, song_id, name, artist, image, youtube_url) VALUES (?,?,?,?,?,?)", 
                            (CURRENT_USER, song.get('song_id'), song['name'], song['artist'], song.get('image',''), song.get('youtube_url','')))
                conn.commit()
                st.toast("Đã thêm vào Bộ sưu tập!")
             else:
                st.toast("Đã có trong danh sách!")
                
        st.markdown("</div>", unsafe_allow_html=True)

    # --- CỘT PHẢI: VIDEO + ĐÁNH GIÁ SAO ---
    with c2:
        if song.get("youtube_url") and pd.notna(song.get("youtube_url")):
            st.video(song["youtube_url"])
        else:
            st.info("Chưa có video preview cho bài hát này.")
            
        st.markdown("### Đánh giá của bạn")
        st.feedback("stars", key="rating_input", on_change=handle_rating)

# 5. MAIN APP LAYOUT
with st.sidebar:
    try: st.image("Logo.png", use_container_width=True)
    except: st.header("V-POP AI")
    
    st.success(f"Xin chào, **{CURRENT_USER}**")
    
    menu_options = ["Khám phá", "Bộ sưu tập", "Thống kê"]
    if "menu_choice" not in st.session_state:
        st.session_state["menu_choice"] = "Khám phá"
    
    def update_menu():
        st.session_state["menu_choice"] = st.session_state["menu_radio_key"]

    menu = st.radio("ĐIỀU HƯỚNG", menu_options, 
                    index=menu_options.index(st.session_state["menu_choice"]),
                    on_change=update_menu, 
                    key="menu_radio_key",
                    label_visibility="collapsed")
    
    st.markdown("---")
    if st.button("Đăng xuất", type="primary", use_container_width=True):
        st.session_state["user_info"] = None
        if "favorites" in st.session_state:
            del st.session_state["favorites"]
        st.rerun()

# --- TAB 1: KHÁM PHÁ ---
if menu == "Khám phá":
    st.title("Trang chủ")
    
    if not stats_df.empty:
        # LOGIC ƯU TIÊN PHÁT TỪ LỊCH SỬ
        if st.session_state["current_song"] is None:
            user_history_df = pd.read_sql_query("SELECT * FROM history WHERE user_id=? ORDER BY timestamp DESC LIMIT 20", conn, params=(CURRENT_USER,))
            
            if not user_history_df.empty:
                hist_song = user_history_df.sample(1).iloc[0].to_dict()
                st.session_state["current_song"] = hist_song
                log_play_event(hist_song)
                st.toast(f"Phát từ Lịch sử: {hist_song['name']}")
            elif st.session_state["favorites"]:
                fav_song = random.choice(st.session_state["favorites"])
                st.session_state["current_song"] = fav_song
                log_play_event(fav_song)
                st.toast(f"Phát từ Yêu thích: {fav_song['name']}")
            else:
                rand_row = stats_df.reset_index().sample(1).iloc[0].to_dict()
                st.session_state["current_song"] = rand_row
                log_play_event(rand_row)
        
        curr = st.session_state["current_song"]
        
        try: 
            if "song_id" in curr and pd.notna(curr["song_id"]):
                s_stats = stats_df.loc[curr["song_id"]].to_dict()
                youtube_url_backup = curr.get('youtube_url')
                curr.update(s_stats)
                if not curr.get('youtube_url'):
                    curr['youtube_url'] = youtube_url_backup
            else:
                match = stats_df.reset_index()
                match = match[(match['name'] == curr['name']) & (match['artist'] == curr['artist'])]
                if not match.empty:
                    curr.update(match.iloc[0].to_dict())
        except: pass
        
        play_song_ui(curr, curr)
        
        st.markdown("---")
        
        with st.expander("Tìm kiếm bài hát khác", expanded=False):
            search = st.text_input("Nhập từ khóa...", label_visibility="collapsed")
            if search:
                keywords = search.lower().split()
                mask = stats_df.reset_index().apply(lambda x: all(k in (str(x['name']) + " " + str(x['artist'])).lower() for k in keywords), axis=1)
                results = stats_df.reset_index()[mask].head(10)
                
                for i, row in results.iterrows():
                    c1, c2, c3 = st.columns([1, 4, 1])
                    with c1: st.image(row['image'], width=60)
                    with c2: 
                        st.write(f"**{row['name']}**")
                        st.caption(row['artist'])
                    with c3:
                        if st.button("Phát", key=f"s_{i}"):
                            st.session_state["current_song"] = row.to_dict()
                            log_play_event(row.to_dict())
                            st.rerun()
                    st.divider()

        st.subheader("Gợi ý tương đồng")
        if recommender:
            recs = recommender.recommend(curr["name"], curr["artist"], top_n=10)
            if recs:
                cols = st.columns(5)
                for i, rec in enumerate(recs):
                    try: r_stats = stats_df.loc[rec["song_id"]]
                    except: r_stats = {}
                    
                    with cols[i % 5]:
                        st.markdown(f"""
                        <div class="song-card">
                            <img src="{rec.get('image', '')}">
                            <div style="font-weight:700; font-size:0.9rem; margin-bottom:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{rec['name']}</div>
                            <div style="font-size:0.8rem; color:#888; margin-bottom:8px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{rec['artist']}</div>
                            <div style="font-size:0.75rem; color:#1DB954; font-weight:600;">Hợp: {rec.get('similarity', 0)*100:.3f}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("Play", key=f"rec_{i}", use_container_width=True):
                            full = rec.copy()
                            if not r_stats.empty: full.update(r_stats.to_dict())
                            st.session_state["current_song"] = full
                            log_play_event(full)
                            st.rerun()
            else:
                st.info("Chưa đủ dữ liệu gợi ý.")

# --- TAB 2: BỘ SƯU TẬP ---
elif menu == "Bộ sưu tập":
    t1, t2 = st.tabs(["Yêu thích", "Lịch sử"])
    
    with t1:
        if not st.session_state["favorites"]:
            st.info("Danh sách trống.")
        else:
            if st.button("Xóa tất cả", type="primary"):
                st.session_state["favorites"] = []
                cur.execute("DELETE FROM favorites WHERE user_id=?", (CURRENT_USER,))
                conn.commit()
                st.rerun()
            
            cols = st.columns(4)
            for i, fav in enumerate(st.session_state["favorites"]):
                with cols[i%4]:
                    st.markdown(f"""
                        <div class="song-card">
                            <img src="{fav.get('image', '')}">
                            <div style="font-weight:bold; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{fav['name']}</div>
                            <div style="font-size:0.8rem; color:#888;">{fav['artist']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    c_a, c_b = st.columns(2)
                    if c_a.button("▶️", key=f"fp_{i}", use_container_width=True):
                        st.session_state["current_song"] = fav
                        log_play_event(fav)
                        st.session_state["menu_choice"] = "Khám phá"
                        st.rerun()
                    if c_b.button("🗑️", key=f"fd_{i}", use_container_width=True):
                        st.session_state["favorites"].pop(i)
                        cur.execute("DELETE FROM favorites WHERE user_id=? AND name=?", (CURRENT_USER, fav['name']))
                        conn.commit()
                        st.rerun()

    with t2:
        hist_df = pd.read_sql_query("SELECT * FROM history WHERE user_id=? ORDER BY timestamp DESC LIMIT 20", conn, params=(CURRENT_USER,))
        if hist_df.empty:
            st.info("Chưa có lịch sử.")
        else:
            for idx, row in hist_df.iterrows():
                c1, c2, c3 = st.columns([1, 8, 2])
                with c1: st.image(row['image'], width=60)
                with c2: 
                    st.write(f"**{row['name']}**")
                    st.caption(f"{row['artist']} • {row['timestamp']}")
                with c3:
                    if st.button("Nghe lại", key=f"h_{idx}"):
                        st.session_state["current_song"] = row.to_dict()
                        log_play_event(row.to_dict())
                        st.session_state["menu_choice"] = "Khám phá"
                        st.rerun()
                st.divider()
# --- TAB 3: THỐNG KÊ
elif menu == "Thống kê":
    st.title("Dashboard Phân tích")
    def altair_dark_theme():
        return {
            "config": {
                "background": "#181818", # Nền của chart
                "font": "Montserrat",
                "title": {"color": "#FFFFFF", "fontSize": 16, "fontWeight": 600, "anchor": "start"},
                "axis": {
                    "labelColor": "#B3B3B3", # Màu chữ trục
                    "titleColor": "#FFFFFF", # Màu tiêu đề trục
                    "grid": False, # Tắt lưới
                    "domainColor": "#555555", # Màu đường trục
                    "tickColor": "#555555"
                },
                "legend": {
                    "labelColor": "#B3B3B3",
                    "titleColor": "#FFFFFF"
                },
                "view": {
                    "stroke": "transparent" # Tắt viền bao
                }
            }
        }
    
    # Áp dụng theme
    alt.themes.register("my_dark_theme", altair_dark_theme)
    alt.themes.enable("my_dark_theme")
    # --- KẾT THÚC ĐỊNH NGHĨA THEME ---
    
    if not stats_df.empty:
        # KPI
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tổng bài hát", f"{len(stats_df):,}")
        c2.metric("Lượt nghe", f"{int(stats_df['play_count'].sum()):,}")
        c3.metric("Rating TB", f"{stats_df[stats_df['rating_count']>0]['avg_rating'].mean():.2f} ⭐")
        c4.metric("Tổng Like", f"{int(stats_df['likes'].sum()):,}")
        
        st.markdown("---")
        
        # --- BỐ CỤC 2x2 CHO BIỂU ĐỒ ---
        c_left, c_right = st.columns(2)
        
        with c_left:
            st.subheader("Top 10 Thịnh Hành (Lượt nghe)")
            top_plays = stats_df.sort_values('play_count', ascending=False).head(10).reset_index()
            chart1 = alt.Chart(top_plays).mark_bar(cornerRadius=5).encode(
                x=alt.X('play_count', title='Lượt nghe'),
                y=alt.Y('name', sort='-x', title=None), # Bỏ tiêu đề trục Y
                color=alt.value('#1DB954'), # Màu xanh brand
                tooltip=['name', 'artist', 'play_count']
            ).properties(height=350)
            st.altair_chart(chart1, use_container_width=True)
            
        with c_right:
            st.subheader("Phân bố Rating")
            rated = stats_df[stats_df['rating_count'] > 0]
            chart2 = alt.Chart(rated).mark_bar().encode(
                x=alt.X('avg_rating', bin=True, title='Điểm Rating (1-5)'),
                y=alt.Y('count()', title='Số lượng bài hát'),
                color=alt.value('#007bff'), # Đổi từ vàng sang xanh dương
                tooltip=['count()']
            ).properties(height=350)
            st.altair_chart(chart2, use_container_width=True)

        st.markdown("---")
        
        col3, col4 = st.columns(2)

        with col3:
            st.subheader("Top 10 Nghệ sĩ (Lượt nghe)")
            artist_stats = stats_df.groupby('artist')['play_count'].sum().reset_index().sort_values('play_count', ascending=False).head(10)
            chart_artist = alt.Chart(artist_stats).mark_bar(cornerRadius=5).encode(
                x=alt.X('play_count', title='Tổng lượt nghe'),
                y=alt.Y('artist', sort='-x', title=None),
                # Gradient xanh chuyên nghiệp
                color=alt.Color('play_count', scale=alt.Scale(range=['#2a4d33', '#1DB954'])), 
                tooltip=['artist', 'play_count']
            ).properties(height=350)
            st.altair_chart(chart_artist, use_container_width=True)

        with col4:
            st.subheader("Tỷ lệ Like / Dislike")
            total_likes = int(stats_df['likes'].sum())
            total_dislikes = int(stats_df['dislikes'].sum())
            interaction_data = pd.DataFrame({'Type': ['Likes', 'Dislikes'], 'Count': [total_likes, total_dislikes]})
            
            # Biểu đồ Donut (Bánh rán)
            base = alt.Chart(interaction_data).encode(
               theta=alt.Theta("Count:Q", stack=True)
            )
            # Màu chuyên nghiệp: Xanh lá và Xám
            pie = base.mark_arc(outerRadius=120, innerRadius=80).encode(
                color=alt.Color("Type:N", scale=alt.Scale(domain=['Likes', 'Dislikes'], range=['#1DB954', '#555555'])),
                order=alt.Order("Count", sort="descending"),
                tooltip=["Type", "Count"]
            )
            text = base.mark_text(radius=140).encode(
                text=alt.Text("Count:Q", format=","),
                order=alt.Order("Count", sort="descending"),
                color=alt.value("white")
            )
            chart_inter = pie + text
            st.altair_chart(chart_inter, use_container_width=True)

conn.close()