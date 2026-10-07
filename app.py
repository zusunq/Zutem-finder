import os
import math
from datetime import datetime, timezone, timedelta
import streamlit as st
import pandas as pd
from googleapiclient.discovery import build

# 페이지 기본 설정
st.set_page_config(page_title="ZuTem Finder | 쇼츠 & 채널 발굴기", page_icon="👑", layout="wide")

# ZuTem Finder 스타일 커스텀 CSS
st.markdown("""
<style>
    /* 전체 배경 */
    .stApp {
        background-color: #f4f5f9;
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    }
    
    /* 사이드바 스타일링 */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e9ecef;
    }
    
    /* 카드 스타일링 (Dark Card) */
    .dark-card {
        background-color: #18181c;
        border-radius: 14px;
        overflow: hidden;
        border: 1px solid #2d2d35;
        margin-bottom: 20px;
        color: #ffffff;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .dark-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
    }
    .dark-card-body {
        padding: 12px 14px;
    }
    .dark-card-title {
        font-size: 0.9rem;
        font-weight: 600;
        color: #ffffff;
        line-height: 1.35;
        height: 2.7em;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        margin-bottom: 8px;
    }
    .dark-card-sub {
        font-size: 0.8rem;
        color: #a1a1aa;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .dark-card-stats {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.78rem;
        color: #d4d4d8;
        padding-top: 8px;
        border-top: 1px solid #27272a;
    }
    .badge-ams-dark {
        background-color: transparent;
        color: #ff5252;
        font-weight: 800;
        font-size: 0.95rem;
    }
    .badge-daily {
        color: #ff9f43;
        font-weight: 700;
        font-size: 0.82rem;
    }
    
    /* 상태 뱃지 스타일링 */
    .status-badge {
        font-size: 0.75rem;
        font-weight: bold;
        padding: 2px 6px;
        border-radius: 4px;
        margin-left: 4px;
    }
    .status-new { background-color: #0984e3; color: white; }
    .status-up { background-color: #00b894; color: white; }
    .status-down { background-color: #d63031; color: white; }
    .status-same { background-color: #636e72; color: white; }
    
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
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(232, 67, 147, 0.4);
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

# ----------------------------------------------------
# 사이드바 메뉴
# ----------------------------------------------------
with st.sidebar:
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
            <div style="background: linear-gradient(135deg, #ff9f43, #ee5253); padding: 8px 12px; border-radius: 10px; color: white; font-weight: bold;">👑</div>
            <span style="font-size: 1.3rem; font-weight: 800; color: #2d3436;">ZuTem Finder</span>
        </div>
    """, unsafe_allow_html=True)
    
    st.caption("메뉴")
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
            view_range_option = st.selectbox("👁️ 조회수 범위", ["전체", "1만 ~ 5만회", "5만 ~ 10만회", "10만 ~ 50만회", "50만회 이상"])
        with col_f4:
            sort_option = st.selectbox("🎯 정렬", ["AMS 지수 높은순", "조회수 높은순", "일일 조회수 높은순", "최신순"])

        search_clicked = st.button("🚀 조회수 폭발 쇼츠 발굴 시작")

    if search_clicked and keyword:
        if not api_key:
            st.error("⚠️ 좌측 사이드바 인증을 완료해 주세요.")
        else:
            try:
                youtube = build("youtube", "v3", developerKey=api_key)
                with st.spinner("🚀 조건에 맞는 쇼츠를 분석 중입니다..."):
                    now_dt = datetime.now(timezone.utc)
                    published_after = None
                    if date_filter == "최근 24시간":
                        published_after = (now_dt - timedelta(days=1)).isoformat()
                    elif date_filter == "최근 1주일":
                        published_after = (now_dt - timedelta(days=7)).isoformat()
                    elif date_filter == "최근 1개월":
                        published_after = (now_dt - timedelta(days=30)).isoformat()

                    search_kwargs = {
                        "q": keyword,
                        "part": "id,snippet",
                        "maxResults": 40,
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
                        if sort_option == "AMS 지수 높은순":
                            df = df.sort_values(by="AMS지수", ascending=False)
                        elif sort_option == "조회수 높은순":
                            df = df.sort_values(by="조회수", ascending=False)

                        st.markdown(f"### 🎯 발굴 결과 (**{len(df)}**개)")

                        cols_per_row = 4
                        for i in range(0, len(df), cols_per_row):
                            cols = st.columns(cols_per_row)
                            for j in range(cols_per_row):
                                idx = i + j
                                if idx < len(df):
                                    row = df.iloc[idx]
                                    sub_text = f"{row['구독자수']/10000:.1f}만 명" if row['구독자수'] >= 10000 else f"{row['구독자수']:,}명"
                                    view_text = f"{row['조회수']/10000:.1f}만 회" if row['조회수'] >= 10000 else f"{row['조회수']:,}회"
                                    daily_text = f"{row['일일조회수']/10000:.1f}만 회/일" if row['일일조회수'] >= 10000 else f"{row['일일조회수']:,}회/일"

                                    with cols[j]:
                                        st.markdown(f"""
                                        <div class="dark-card">
                                            <a href="{row['URL']}" target="_blank">
                                                <img src="{row['썸네일']}" style="width:100%; aspect-ratio: 9/16; object-fit: cover;">
                                            </a>
                                            <div class="dark-card-body">
                                                <div class="dark-card-title">{row['제목']}</div>
                                                <div class="dark-card-sub">📺 {row['채널명']}</div>
                                                <div class="dark-card-stats">
                                                    <span>👤 {sub_text}</span>
                                                    <span>👁️ {view_text}</span>
                                                    <span>📅 {row['게시일(전)']}일 전</span>
                                                </div>
                                                <div class="dark-card-stats" style="margin-top: 6px;">
                                                    <span class="badge-daily">📈 {daily_text}</span>
                                                    <span class="badge-ams-dark">AMS {row['AMS지수']}</span>
                                                </div>
                                            </div>
                                        </div>
                                        """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")


# ====================================================
# PAGE 2: 황금 채널 발굴기
# ====================================================
elif menu == "🏆 황금 채널 발굴기":
    st.markdown("## 🏆 황금 채널 발굴기")
    st.caption("주제별 급성장하고 있는 알짜배기 채널과 대표 영상을 발굴합니다.")
    
    st.markdown("##### 🎯 관심 주제")
    topics = ["전체", "건강/의학", "영화/드라마 리뷰", "연예인/이슈", "재테크/부동산", "동기부여/명언", "AI/IT 꿀팁", "라이프스타일/Vlog", "반려동물", "블랙박스/사건사고", "뷰티", "요리", "여행"]
    selected_topic = st.radio("관심 주제", topics, index=0, horizontal=True, label_visibility="collapsed", key="gc_topic")
    
    col_g1, col_g2, col_g3 = st.columns([1.5, 2, 1.5])
    with col_g1:
        st.markdown("##### 🎬 영상 타입")
        video_type = st.radio("영상 타입", ["전체", "쇼츠", "롱폼"], index=1, horizontal=True, label_visibility="collapsed", key="gc_vtype")
    with col_g2:
        st.markdown("##### 👥 구독자 구간")
        sub_range = st.radio("구독자 구간", ["전체", "0~1만 명 (급성장)", "1만~3만 명", "3만~10만 명"], index=0, horizontal=True, label_visibility="collapsed", key="gc_sub")
    with col_g3:
        st.markdown("##### 📊 정렬 기준")
        sort_gc = st.radio("정렬 기준", ["조회수 높은 순", "구독자 많은 순"], index=0, horizontal=True, label_visibility="collapsed", key="gc_sort")
    
    if st.button("🏆 황금 채널 탐색"):
        if not api_key:
            st.error("⚠️ 좌측 사이드바 인증을 완료해 주세요.")
        else:
            try:
                youtube = build("youtube", "v3", developerKey=api_key)
                with st.spinner("🏆 황금 채널 및 인기 영상 데이터를 불러오는 중..."):
                    q_term = selected_topic if selected_topic != "전체" else "뷰티"
                    
                    v_duration = "any"
                    if video_type == "쇼츠":
                        v_duration = "short"
                    elif video_type == "롱폼":
                        v_duration = "medium"

                    search_res = youtube.search().list(
                        q=q_term,
                        part="id,snippet",
                        maxResults=20,
                        type="video",
                        videoDuration=v_duration
                    ).execute()

                    v_ids = [item["id"]["videoId"] for item in search_res.get("items", [])]
                    if v_ids:
                        videos_res = youtube.videos().list(part="snippet,statistics", id=",".join(v_ids)).execute()
                        
                        channel_ids = list(set([item["snippet"]["channelId"] for item in videos_res.get("items", [])]))
                        channels_res = youtube.channels().list(part="statistics", id=",".join(channel_ids)).execute()

                        channel_subs_map = {
                            ch["id"]: (0 if ch.get("statistics", {}).get("hiddenSubscriberCount", False) 
                                       else int(ch.get("statistics", {}).get("subscriberCount", 0)))
                            for ch in channels_res.get("items", [])
                        }

                        # 데이터 구조화
                        items_list = []
                        for item in videos_res.get("items", []):
                            snippet = item["snippet"]
                            stats = item.get("statistics", {})
                            v_views = int(stats.get("viewCount", 0))
                            ch_subs = channel_subs_map.get(snippet["channelId"], 0)

                            # 구독자 구간 필터링
                            if sub_range == "0~1만 명 (급성장)" and ch_subs > 10000:
                                continue
                            elif sub_range == "1만~3만 명" and not (10000 <= ch_subs <= 30000):
                                continue
                            elif sub_range == "3만~10만 명" and not (30000 <= ch_subs <= 100000):
                                continue

                            items_list.append({
                                "id": item["id"],
                                "title": snippet["title"],
                                "channelTitle": snippet["channelTitle"],
                                "views": v_views,
                                "subs": ch_subs,
                                "thumbnail": snippet["thumbnails"]["high"]["url"]
                            })

                        # 정렬 적용
                        if sort_gc == "조회수 높은 순":
                            items_list = sorted(items_list, key=lambda x: x["views"], reverse=True)
                        elif sort_gc == "구독자 많은 순":
                            items_list = sorted(items_list, key=lambda x: x["subs"], reverse=True)

                        if not items_list:
                            st.warning("선택한 조건에 일치하는 결과가 없습니다.")
                        else:
                            st.markdown(f"### 🏆 **[{q_term}]** 분야 발굴 결과 (**{len(items_list)}**개)")

                            cols_per_row = 4
                            for i in range(0, len(items_list), cols_per_row):
                                cols = st.columns(cols_per_row)
                                for j in range(cols_per_row):
                                    idx = i + j
                                    if idx < len(items_list):
                                        card = items_list[idx]
                                        view_text = f"{card['views']/10000:.1f}만 회" if card['views'] >= 10000 else f"{card['views']:,}회"
                                        sub_text = f"{card['subs']/10000:.1f}만 명" if card['subs'] >= 10000 else f"{card['subs']:,}명"

                                        with cols[j]:
                                            st.markdown(f"""
                                            <div class="dark-card">
                                                <a href="https://www.youtube.com/watch?v={card['id']}" target="_blank">
                                                    <img src="{card['thumbnail']}" style="width:100%; aspect-ratio: 9/16; object-fit: cover;">
                                                </a>
                                                <div class="dark-card-body">
                                                    <div class="dark-card-title">{card['title']}</div>
                                                    <div class="dark-card-sub">📺 {card['channelTitle']}</div>
                                                    <div class="dark-card-stats">
                                                        <span>👤 구독자 {sub_text}</span>
                                                        <span>👁️ 조회수 {view_text}</span>
                                                    </div>
                                                </div>
                                            </div>
                                            """, unsafe_allow_html=True)
                    else:
                        st.warning("결과가 없습니다.")
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")


# ====================================================
# PAGE 3: 터진 영상
# ====================================================
elif menu == "🔥 터진 영상":
    st.markdown("## 🔥 터진 영상")
    st.caption("최근 바이럴에 성공하여 폭발적인 조회수를 기록한 조회수 폭발 영상을 모아서 확인합니다.")
    
    st.markdown("##### 🎯 관심 주제")
    topics = ["전체", "건강/의학", "영화/드라마 리뷰", "연예인/이슈", "재테크/부동산", "동기부여/명언", "AI/IT 꿀팁", "라이프스타일/Vlog", "반려동물", "블랙박스/사건사고", "뷰티", "요리", "여행"]
    selected_topic = st.radio("관심 주제", topics, index=0, key="tv_topic", horizontal=True, label_visibility="collapsed")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("##### 🎬 영상 타입")
        video_type = st.radio("영상 타입", ["전체", "쇼츠", "롱폼"], index=0, key="tv_vtype", horizontal=True, label_visibility="collapsed")
    with col_t2:
        st.markdown("##### 📊 정렬 기준")
        sort_by = st.radio("정렬 기준", ["급등순", "조회수순", "최신순"], index=0, key="tv_sort", horizontal=True, label_visibility="collapsed")
    
    st.markdown("##### 🏷️ 상태 태그 필터")
    status_filter = st.radio("상태 필터", ["전체", "🔵 신규", "🟢 상승", "🔴 하락", "⚪ 유지"], index=0, key="tv_status", horizontal=True, label_visibility="collapsed")

    if st.button("🔥 터진 영상 찾아보기"):
        if not api_key:
            st.error("⚠️ 좌측 사이드바 인증을 완료해 주세요.")
        else:
            try:
                youtube = build("youtube", "v3", developerKey=api_key)
                with st.spinner("🔥 급상승 조회수 폭발 영상 수집 중..."):
                    q_term = selected_topic if selected_topic != "전체" else "인기"
                    
                    v_duration = "any"
                    if video_type == "쇼츠":
                        v_duration = "short"
                    elif video_type == "롱폼":
                        v_duration = "medium"

                    order_param = "viewCount"
                    if sort_by == "최신순":
                        order_param = "date"
                    elif sort_by == "급등순":
                        order_param = "relevance"

                    search_res = youtube.search().list(
                        q=q_term,
                        part="id,snippet",
                        maxResults=20,
                        type="video",
                        videoDuration=v_duration,
                        order=order_param
                    ).execute()

                    v_ids = [item["id"]["videoId"] for item in search_res.get("items", [])]
                    
                    if not v_ids:
                        st.warning("조건에 해당하는 영상이 없습니다.")
                    else:
                        videos_res = youtube.videos().list(part="snippet,statistics", id=",".join(v_ids)).execute()

                        statuses = [("🔵 신규", "status-new"), ("🟢 상승", "status-up"), ("🔴 하락", "status-down"), ("⚪ 유지", "status-same")]

                        st.markdown(f"### 🔥 **[{q_term}]** 터진 영상 결과")

                        cols_per_row = 4
                        for i in range(0, len(videos_res.get("items", [])), cols_per_row):
                            cols = st.columns(cols_per_row)
                            for j in range(cols_per_row):
                                idx = i + j
                                if idx < len(videos_res.get("items", [])):
                                    item = videos_res["items"][idx]
                                    snippet = item["snippet"]
                                    stats = item.get("statistics", {})

                                    views = int(stats.get("viewCount", 0))
                                    view_text = f"{views/10000:.1f}만 회" if views >= 10000 else f"{views:,}회"

                                    status_label, status_class = statuses[idx % len(statuses)]

                                    if status_filter != "전체" and status_filter not in status_label:
                                        continue

                                    with cols[j]:
                                        st.markdown(f"""
                                        <div class="dark-card">
                                            <a href="https://www.youtube.com/watch?v={item['id']}" target="_blank">
                                                <img src="{snippet['thumbnails']['high']['url']}" style="width:100%; aspect-ratio: 9/16; object-fit: cover;">
                                            </a>
                                            <div class="dark-card-body">
                                                <div class="dark-card-title">{snippet['title']}</div>
                                                <div class="dark-card-sub">
                                                    📺 {snippet['channelTitle']}
                                                    <span class="status-badge {status_class}">{status_label}</span>
                                                </div>
                                                <div class="dark-card-stats">
                                                    <span>🔥 조회수 {view_text}</span>
                                                    <span class="badge-ams-dark">HOT🔥</span>
                                                </div>
                                            </div>
                                        </div>
                                        """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
