import os
import math
from datetime import datetime, timezone, timedelta
import streamlit as st
import pandas as pd
from googleapiclient.discovery import build

# 페이지 기본 설정
st.set_page_config(page_title="ZuTem Finder | 쇼츠 & 채널 발굴기", page_icon="👑", layout="wide")

# ZuTem Finder 스타일 커스텀 CSS (이미지 스타일 적용)
st.markdown("""
<style>
    /* 전체 배경 */
    .stApp {
        background-color: #0d0e12;
        color: #ffffff;
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    }
    
    /* 사이드바 스타일링 */
    [data-testid="stSidebar"] {
        background-color: #16181d;
        border-right: 1px solid #232730;
    }
    
    /* 카드 스타일링 (Dark Card - 이미지 디자인 재현) */
    .dark-card {
        background-color: #17191e;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #282c37;
        margin-bottom: 20px;
        color: #ffffff;
        position: relative;
    }
    
    .thumbnail-container {
        position: relative;
        width: 100%;
        aspect-ratio: 9/16;
        background-color: #000;
    }
    .thumbnail-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    
    /* 카드 상단 오버레이 버튼들 */
    .top-left-btn {
        position: absolute;
        top: 8px;
        left: 8px;
        background: rgba(255, 255, 255, 0.85);
        border: none;
        border-radius: 50%;
        width: 28px;
        height: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        cursor: pointer;
    }
    .top-right-btns {
        position: absolute;
        top: 8px;
        right: 8px;
        display: flex;
        gap: 4px;
    }
    .overlay-btn {
        background: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(4px);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 3px 8px;
        font-size: 0.7rem;
        font-weight: bold;
    }

    .dark-card-body {
        padding: 12px;
    }
    .dark-card-title {
        font-size: 0.88rem;
        font-weight: 700;
        color: #ffffff;
        line-height: 1.35;
        height: 2.7em;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        margin-bottom: 10px;
    }
    
    .channel-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    .channel-info {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.78rem;
        color: #a1a1aa;
    }
    .channel-badge {
        background-color: #3b3e4a;
        color: #d1d5db;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.7rem;
    }
    .analyze-btn {
        background-color: #1e3a3a;
        color: #2dd4bf;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: bold;
    }
    
    /* 3열 데이터 (구독자 | 조회수 | 업로드) */
    .stats-3col {
        display: grid;
        grid-template-columns: 1fr 1.2fr 1fr;
        gap: 2px;
        background-color: #1f222a;
        padding: 8px 6px;
        border-radius: 6px;
        text-align: center;
        margin-bottom: 10px;
    }
    .stats-item-title {
        font-size: 0.65rem;
        color: #80838e;
        margin-bottom: 2px;
    }
    .stats-item-val {
        font-size: 0.8rem;
        font-weight: 700;
        color: #ffffff;
    }
    
    /* 일일 조회수 및 AMS 지수 */
    .daily-row {
        display: flex;
        justify-content: space-between;
        font-size: 0.75rem;
        color: #a1a1aa;
        margin-bottom: 4px;
    }
    .daily-val {
        color: #ff9f43;
        font-weight: bold;
    }
    .ams-row {
        display: flex;
        justify-content: space-between;
        font-size: 0.82rem;
        font-weight: bold;
        color: #ffffff;
        margin-bottom: 8px;
    }
    .ams-val {
        color: #ff9f43;
        font-size: 0.95rem;
    }
    
    .card-footer-line {
        height: 3px;
        background: linear-gradient(90deg, #ff9f43, #ee5253);
        border-radius: 2px;
    }
    
    /* 버튼 스타일링 */
    .stButton>button {
        background: linear-gradient(90deg, #8e44ad 0%, #e84393 100%);
        color: white !important;
        border: none;
        border-radius: 12px;
        font-weight: 700;
        height: 52px;
        font-size: 1.1rem;
        width: 100%;
        box-shadow: 0 4px 15px rgba(232, 67, 147, 0.3);
        transition: all 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

# Secrets 안전 불러오기
real_api_key = ""
correct_password = ""
try:
    real_api_key = st.secrets.get("YOUTUBE_API_KEY", "")
    correct_password = st.secrets.get("MY_PASSWORD", "")
except Exception:
    pass

# 사이드바 메뉴
with st.sidebar:
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
            <div style="background: linear-gradient(135deg, #ff9f43, #ee5253); padding: 8px 12px; border-radius: 10px; color: white; font-weight: bold;">👑</div>
            <span style="font-size: 1.3rem; font-weight: 800; color: #ffffff;">ZuTem Finder</span>
        </div>
    """, unsafe_allow_html=True)
    
    menu = st.radio(
        "메뉴 선택",
        ["🔍 조회수 폭발 쇼츠 찾기", "🏆 황금 채널 발굴기", "🔥 터진 영상"],
        label_visibility="collapsed"
    )
    
    st.divider()
    st.markdown("### 🔑 접속 인증")
    user_input_pw = st.text_input("비밀번호 입력", type="password", placeholder="비밀번호를 입력하세요")
    
    if user_input_pw == correct_password and correct_password != "":
        api_key = real_api_key
        st.success("인증 완료!")
    else:
        api_key = ""
        if user_input_pw:
            st.error("비밀번호 불일치")
        else:
            st.info("비밀번호를 입력해야 서비스가 활성화됩니다.")

# AMS 계산 함수
def calculate_ams(subscribers, views, days_passed):
    daily_views = views / max(days_passed, 1)
    subs_base = max(subscribers, 100)
    ratio = views / subs_base
    
    if ratio <= 0:
        ams_score = 0.0
    else:
        raw_score = 70 + (math.log10(ratio + 1) * 15)
        ams_score = min(round(raw_score, 1), 99.9)
        if ratio < 0.5:
            ams_score = round(ratio * 100, 1)

    return round(daily_views), ams_score


# ====================================================
# PAGE 1: 조회수 폭발 쇼츠 찾기
# ====================================================
if menu == "🔍 조회수 폭발 쇼츠 찾기":
    st.markdown("## 🔍 조회수 폭발 쇼츠 찾기")
    st.caption("조건에 부합하는 알고리즘 조회수 폭발 쇼츠를 신속하게 검색합니다.")
    
    with st.container():
        keyword = st.text_input("검색어", placeholder="검색어를 입력하세요 (예: 요리, 운동, 재테크, 꿀템...)", label_visibility="collapsed")
        
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1:
            date_filter = st.selectbox("📅 업로드 일자", ["최근 1주일", "최근 24시간", "최근 1개월", "최근 1년", "전체"])
        with col_f2:
            max_subs_option = st.selectbox("👥 최대 구독자", ["제한 없음", "1만 명 이하", "5만 명 이하", "10만 명 이하", "50만 명 이하"])
        with col_f3:
            # 📌 이미지 1의 옵션 항목으로 완전 변경
            view_range_option = st.selectbox("👁️ 조회수 범위", ["전체", "1만 ~ 5만회", "5만 ~ 10만회", "10만 ~ 30만회", "30만 ~ 100만회", "100만회 이상"])
        with col_f4:
            sort_option = st.selectbox("🎯 정렬", ["AMS 지수 높은순", "조회수 높은순", "일일 조회수 높은순", "최신순"])

        search_clicked = st.button("🚀 떡상 쇼츠 발굴 시작")

    if search_clicked and keyword:
        if not api_key:
            st.error("⚠️ 좌측 사이드바 인증을 완료해 주세요.")
        else:
            try:
                youtube = build("youtube", "v3", developerKey=api_key)
                with st.spinner("🚀 조건에 맞는 쇼츠를 분석 중입니다..."):
                    now_dt = datetime.now(timezone.utc)
                    published_after = None
                    
                    # 📌 업로드 일자 필터링 (최근 1년 옵션 추가)
                    if date_filter == "최근 24시간":
                        published_after = (now_dt - timedelta(days=1)).isoformat()
                    elif date_filter == "최근 1주일":
                        published_after = (now_dt - timedelta(days=7)).isoformat()
                    elif date_filter == "최근 1개월":
                        published_after = (now_dt - timedelta(days=30)).isoformat()
                    elif date_filter == "최근 1년":
                        published_after = (now_dt - timedelta(days=365)).isoformat()

                    search_kwargs = {
                        "q": keyword,
                        "part": "id,snippet",
                        "maxResults": 50,
                        "type": "video",
                        "videoDuration": "short"
                    }
                    if published_after:
                        search_kwargs["publishedAfter"] = published_after

                    search_response = youtube.search().list(**search_kwargs).execute()
                    video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]

                    if not video_ids:
                        st.warning("검색 결과가 없습니다.")
                    else:
                        videos_response = youtube.videos().list(part="snippet,statistics", id=",".join(video_ids)).execute()
                        channel_ids = list(set([item["snippet"]["channelId"] for item in videos_response["items"]]))
                        channels_response = youtube.channels().list(part="statistics", id=",".join(channel_ids)).execute()

                        channel_subs_map = {
                            ch["id"]: (0 if ch.get("statistics", {}).get("hiddenSubscriberCount", False) 
                                       else int(ch.get("statistics", {}).get("subscriberCount", 0)))
                            for ch in channels_response.get("items", [])
                        }

                        data_list = []
                        for item in videos_response.get("items", []):
                            v_id = item["id"]
                            snippet = item["snippet"]
                            stats = item.get("statistics", {})

                            published_at = datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00"))
                            days_passed = max((now_dt - published_at).days, 1)

                            views = int(stats.get("viewCount", 0))
                            subscribers = channel_subs_map.get(snippet["channelId"], 0)

                            # 📌 최대 구독자 조건 필터링
                            if max_subs_option == "1만 명 이하" and subscribers > 10000:
                                continue
                            elif max_subs_option == "5만 명 이하" and subscribers > 50000:
                                continue
                            elif max_subs_option == "10만 명 이하" and subscribers > 100000:
                                continue
                            elif max_subs_option == "50만 명 이하" and subscribers > 500000:
                                continue

                            # 📌 조회수 범위 조건 필터링
                            if view_range_option == "1만 ~ 5만회" and not (10000 <= views < 50000):
                                continue
                            elif view_range_option == "5만 ~ 10만회" and not (50000 <= views < 100000):
                                continue
                            elif view_range_option == "10만 ~ 30만회" and not (100000 <= views < 300000):
                                continue
                            elif view_range_option == "30만 ~ 100만회" and not (300000 <= views < 1000000):
                                continue
                            elif view_range_option == "100만회 이상" and views < 1000000:
                                continue

                            daily_views, ams_score = calculate_ams(subscribers, views, days_passed)

                            data_list.append({
                                "video_id": v_id,
                                "제목": snippet["title"],
                                "채널명": snippet["channelTitle"],
                                "구독자수": subscribers,
                                "조회수": views,
                                "일일조회수": daily_views,
                                "AMS지수": ams_score,
                                "게시일(전)": days_passed,
                                "URL": f"https://www.youtube.com/shorts/{v_id}",
                                "썸네일": snippet["thumbnails"]["high"]["url"]
                            })

                        df = pd.DataFrame(data_list)
                        if not df.empty:
                            if sort_option == "AMS 지수 높은순":
                                df = df.sort_values(by="AMS지수", ascending=False)
                            elif sort_option == "조회수 높은순":
                                df = df.sort_values(by="조회수", ascending=False)
                            elif sort_option == "일일 조회수 높은순":
                                df = df.sort_values(by="일일조회수", ascending=False)
                            elif sort_option == "최신순":
                                df = df.sort_values(by="게시일(전)", ascending=True)

                        st.markdown(f"### 발견된 영상 **{len(df)}**개")

                        if df.empty:
                            st.warning("선택한 필터 조건에 알맞은 영상이 없습니다.")
                        else:
                            cols_per_row = 4
                            for i in range(0, len(df), cols_per_row):
                                cols = st.columns(cols_per_row)
                                for j in range(cols_per_row):
                                    idx = i + j
                                    if idx < len(df):
                                        row = df.iloc[idx]
                                        sub_text = f"{row['구독자수']/10000:.1f}만명" if row['구독자수'] >= 10000 else f"{row['구독자수']:,}명"
                                        view_text = f"{row['조회수']/10000:.1f}만 회" if row['조회수'] >= 10000 else f"{row['조회수']:,}회"
                                        daily_text = f"{row['일일조회수']/10000:.1f}만 회/일" if row['일일조회수'] >= 10000 else f"{row['일일조회수']:,}회/일"

                                        # 📌 이미지 2와 동일한 결과 카드 레이아웃 구현
                                        with cols[j]:
                                            st.markdown(f"""
                                            <div class="dark-card">
                                                <div class="thumbnail-container">
                                                    <a href="{row['URL']}" target="_blank">
                                                        <img class="thumbnail-img" src="{row['썸네일']}">
                                                    </a>
                                                    <div class="top-left-btn">☆</div>
                                                    <div class="top-right-btns">
                                                        <span class="overlay-btn">📝 대본</span>
                                                        <span class="overlay-btn">썸네일</span>
                                                    </div>
                                                </div>
                                                <div class="dark-card-body">
                                                    <div class="dark-card-title">{row['제목']}</div>
                                                    <div class="channel-row">
                                                        <div class="channel-info">
                                                            <span class="channel-badge">📺</span>
                                                            <span>{row['채널명']}</span>
                                                        </div>
                                                        <span class="analyze-btn">📊 분석</span>
                                                    </div>
                                                    <div class="stats-3col">
                                                        <div>
                                                            <div class="stats-item-title">구독자</div>
                                                            <div class="stats-item-val">{sub_text}</div>
                                                        </div>
                                                        <div>
                                                            <div class="stats-item-title">조회수</div>
                                                            <div class="stats-item-val">{view_text}</div>
                                                        </div>
                                                        <div>
                                                            <div class="stats-item-title">업로드</div>
                                                            <div class="stats-item-val">{row['게시일(전)']}일 전</div>
                                                        </div>
                                                    </div>
                                                    <div class="daily-row">
                                                        <span>일일 조회수</span>
                                                        <span class="daily-val">{daily_text}</span>
                                                    </div>
                                                    <div class="ams-row">
                                                        <span>AMS 지수</span>
                                                        <span class="ams-val">{row['AMS지수']}</span>
                                                    </div>
                                                    <div class="card-footer-line"></div>
                                                </div>
                                            </div>
                                            """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")

# (이하 황금 채널 발굴기 및 터진 영상 페이지는 기존과 동일)
