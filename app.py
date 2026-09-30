import os
import math
from datetime import datetime, timezone, timedelta
import streamlit as st
import pandas as pd
from googleapiclient.discovery import build

# 페이지 설정 & 커스텀 CSS 적용
st.set_page_config(page_title="Zutem Finder Style Shorts Search", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    /* 메인 배경 및 폰트 세팅 */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* 카드 스타일링 */
    .shorts-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border: 1px solid #e9ecef;
        margin-bottom: 20px;
        transition: transform 0.2s ease-in-out;
    }
    .shorts-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
    }
    
    /* 뱃지 스타일링 */
    .badge-ams {
        background-color: #ff4757;
        color: white;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 0.85rem;
    }
    .badge-info {
        background-color: #eccc68;
        color: #2f3542;
        padding: 3px 6px;
        border-radius: 4px;
        font-size: 0.8rem;
    }
    
    /* 버튼 스타일링 */
    .stButton>button {
        background: linear-gradient(90deg, #ff416c 0%, #ff4b2b 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        height: 48px;
        font-size: 1.05rem;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Zutem Finder | 유튜브 영상 및 채널 발굴기")

# 사이드바 설정
with st.sidebar:
    st.header("📌 메뉴 선택")
    menu = st.radio(
        "기능을 선택하세요:",
        ["⚡ 조회수 폭발 쇼츠 찾기", "🏆 황금채널 발굴기", "🔥 터진영상"]
    )
    st.divider()

    st.header("🔑 접속 인증")
    
    # Secrets에 저장된 API 키와 비밀번호 불러오기
    real_api_key = st.secrets.get("YOUTUBE_API_KEY", "")
    correct_password = st.secrets.get("MY_PASSWORD", "")
    
    # 비밀번호 입력창
    user_input_pw = st.text_input("접속 비밀번호 입력", type="password", help="서비스 이용을 위한 비밀번호를 입력하세요.")
    
    # 비밀번호 일치 여부 검증
    if user_input_pw == correct_password and correct_password != "":
        api_key = real_api_key
        st.success("인증 완료! 서비스를 이용할 수 있습니다.")
    else:
        api_key = ""
        if user_input_pw:
            st.error("비밀번호가 올바르지 않습니다.")
        else:
            st.info("비밀번호를 입력해야 서비스가 활성화됩니다.")
            
    st.divider()
    st.markdown("💡 **Zutem Finder 안내**")
    st.caption("키워드를 검색하고 조건별 필터를 지정하면 알고리즘 상승 지수(AMS) 및 떡상 콘텐츠를 검색할 수 있습니다.")

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

# 공통 태그 UI 렌더링 함수 (이미지 속 관심주제/영상타입/구독자구간)
def render_common_filters():
    st.markdown("#### 🎯 관심 주제")
    topics = ["전체", "건강/의학", "영화/드라마 리뷰", "연예인/이슈", "재테크/부동산", "동기부여/명언", "AI/IT 꿀팁", "라이프스타일/Vlog", "반려동물", "블랙박스/사건사고", "뷰티", "요리", "여행"]
    selected_topic = st.segmented_control("주제 선택", topics, default="전체")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### 🎬 영상 타입")
        video_type = st.segmented_control("타입 선택", ["전체", "쇼츠", "롱폼"], default="쇼츠")
    with col_b:
        st.markdown("#### 👥 구독자 구간")
        sub_range = st.segmented_control("구독자 범위", ["전체", "0~1만 명 (급성장)", "1만~5만 명", "5만~10만 명"], default="전체")

    sort_by = st.radio("🎯 정렬 기준", ["조회수 높은 순", "구독자 많은 순", "AMS 지수 높은 순"], horizontal=True)
    return selected_topic, video_type, sub_range, sort_by


# ==========================================
# 1. 조회수 폭발 쇼츠 찾기 (기존 기능)
# ==========================================
if menu == "⚡ 조회수 폭발 쇼츠 찾기":
    st.subheader("⚡ 조회수 폭발 쇼츠 발굴기")
    st.caption("유튜브 알고리즘을 분석하여 빠른 속도로 성장하는 떡상 쇼츠를 검색·비교합니다.")

    keyword = st.text_input("🔍 검색 키워드", placeholder="예: 연예인추천템, 코스트코 추천, 꿀템")

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        date_filter = st.selectbox("📅 업로드 일자", ["전체", "최근 24시간", "최근 7일", "최근 1개월", "최근 1년"])
    with col_f2:
        max_subs_option = st.selectbox("👥 최대 구독자", ["제한 없음", "1만 명 이하", "5만 명 이하", "10만 명 이하", "50만 명 이하"])
    with col_f3:
        view_range_option = st.selectbox("👁️ 조회수 범위", ["전체", "1만 ~ 10만회", "10만 ~ 50만회", "50만 ~ 100만회", "100만회 이상"])
    with col_f4:
        sort_option = st.selectbox("🎯 정렬 기준", ["AMS 지수 높은순", "조회수 높은순", "일일 조회수 높은순", "최신순"])

    search_clicked = st.button("🚀 떡상 쇼츠 발굴 시작")

    if search_clicked and keyword:
        if not api_key:
            st.error("⚠️ 좌측 사이드바에 YouTube Data API 키와 비밀번호를 먼저 확인해 주세요!")
        else:
            try:
                youtube = build("youtube", "v3", developerKey=api_key)
                
                with st.spinner("🔍 조건에 부합하는 쇼츠 데이터를 분석 중입니다..."):
                    now_dt = datetime.now(timezone.utc)
                    published_after = None
                    if date_filter == "최근 24시간":
                        published_after = (now_dt - timedelta(days=1)).isoformat()
                    elif date_filter == "최근 7일":
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
                        st.warning("조건에 해당하는 검색 결과가 없습니다.")
                    else:
                        videos_response = youtube.videos().list(
                            part="snippet,statistics",
                            id=",".join(video_ids)
                        ).execute()

                        channel_ids = list(set([item["snippet"]["channelId"] for item in videos_response["items"]]))
                        channels_response = youtube.channels().list(
                            part="statistics",
                            id=",".join(channel_ids)
                        ).execute()

                        channel_subs_map = {}
                        for ch in channels_response.get("items", []):
                            ch_stats = ch.get("statistics", {})
                            subs = 0 if ch_stats.get("hiddenSubscriberCount", False) else int(ch_stats.get("subscriberCount", 0))
                            channel_subs_map[ch["id"]] = subs

                        data_list = []
                        for item in videos_response.get("items", []):
                            v_id = item["id"]
                            snippet = item["snippet"]
                            stats = item.get("statistics", {})

                            title = snippet["title"]
                            channel_title = snippet["channelTitle"]
                            channel_id = snippet["channelId"]
                            published_at = datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00"))
                            days_passed = max((now_dt - published_at).days, 1)

                            views = int(stats.get("viewCount", 0))
                            subscribers = channel_subs_map.get(channel_id, 0)

                            if max_subs_option == "1만 명 이하" and subscribers > 10000: continue
                            elif max_subs_option == "5만 명 이하" and subscribers > 50000: continue
                            elif max_subs_option == "10만 명 이하" and subscribers > 100000: continue
                            elif max_subs_option == "50만 명 이하" and subscribers > 500000: continue

                            if view_range_option == "1만 ~ 10만회" and not (10000 <= views < 100000): continue
                            elif view_range_option == "10만 ~ 50만회" and not (100000 <= views < 500000): continue
                            elif view_range_option == "50만 ~ 100만회" and not (500000 <= views < 1000000): continue
                            elif view_range_option == "100만회 이상" and views < 1000000: continue

                            daily_views, ams_score = calculate_ams(subscribers, views, days_passed)

                            data_list.append({
                                "video_id": v_id,
                                "제목": title,
                                "채널명": channel_title,
                                "구독자수": subscribers,
                                "조회수": views,
                                "일일조회수": daily_views,
                                "AMS지수": ams_score,
                                "게시일(전)": days_passed,
                                "URL": f"https://www.youtube.com/shorts/{v_id}",
                                "썸네일": snippet["thumbnails"]["high"]["url"]
                            })

                        if not data_list:
                            st.warning("지정한 필터 조건을 만족하는 쇼츠가 없습니다.")
                        else:
                            df = pd.DataFrame(data_list)

                            if sort_option == "AMS 지수 높은순":
                                df = df.sort_values(by="AMS지수", ascending=False)
                            elif sort_option == "조회수 높은순":
                                df = df.sort_values(by="조회수", ascending=False)
                            elif sort_option == "일일 조회수 높은순":
                                df = df.sort_values(by="일일조회수", ascending=False)
                            elif sort_option == "최신순":
                                df = df.sort_values(by="게시일(전)", ascending=True)

                            df = df.reset_index(drop=True)
                            st.markdown(f"### 🎉 발견된 영상 **{len(df)}**개")

                            cols_per_row = 4
                            for i in range(0, len(df), cols_per_row):
                                cols = st.columns(cols_per_row)
                                for j in range(cols_per_row):
                                    idx = i + j
                                    if idx < len(df):
                                        row = df.iloc[idx]
                                        with cols[j]:
                                            sub_str = f"{row['구독자수']:,}명" if row['구독자수'] > 0 else "비공개"
                                            st.markdown(f"""
                                            <div class="shorts-card">
                                                <a href="{row['URL']}" target="_blank">
                                                    <img src="{row['썸네일']}" style="width:100%; border-radius:8px; margin-bottom:10px;">
                                                </a>
                                                <div style="font-weight:bold; font-size:0.95rem; line-height:1.3; height:2.6em; overflow:hidden; text-overflow:ellipsis; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; margin-bottom:8px;">
                                                    <a href="{row['URL']}" target="_blank" style="text-decoration:none; color:#212529;">{row['제목']}</a>
                                                </div>
                                                <div style="color:#6c757d; font-size:0.85rem; margin-bottom:12px;">📺 {row['채널명']}</div>
                                                <hr style="margin:8px 0; border:none; border-top:1px solid #f1f3f5;">
                                                <div style="font-size:0.8rem; color:#495057; display:flex; justify-content:space-between; margin-bottom:4px;">
                                                    <span>👤 구독자</span> <b>{sub_str}</b>
                                                </div>
                                                <div style="font-size:0.8rem; color:#495057; display:flex; justify-content:space-between; margin-bottom:4px;">
                                                    <span>👁️ 조회수</span> <b>{row['조회수']:,}회</b>
                                                </div>
                                                <div style="font-size:0.8rem; color:#495057; display:flex; justify-content:space-between; margin-bottom:8px;">
                                                    <span>📅 업로드</span> <b>{row['게시일(전)']}일 전</b>
                                                </div>
                                                <div style="background-color:#f1f3f5; padding:8px; border-radius:6px; font-size:0.8rem; display:flex; justify-content:space-between; align-items:center;">
                                                    <span>📈 일일 조회수</span>
                                                    <span style="color:#e67e22; font-weight:bold;">{row['일일조회수']:,}회/일</span>
                                                </div>
                                                <div style="margin-top:8px; background-color:#fff5f5; padding:8px; border-radius:6px; font-size:0.85rem; display:flex; justify-content:space-between; align-items:center; border:1px solid #ffe3e3;">
                                                    <span style="font-weight:bold; color:#e03131;">🔥 AMS 지수</span>
                                                    <span style="font-weight:bold; color:#e03131; font-size:1rem;">{row['AMS지수']}</span>
                                                </div>
                                            </div>
                                            """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")


# ==========================================
# 2. 황금채널 발굴기
# ==========================================
elif menu == "🏆 황금채널 발굴기":
    st.subheader("🏆 황금 채널 발굴기")
    st.caption("구독자 대비 뛰어난 조회수 성과를 내는 알짜배기 '황금 채널'을 발굴합니다.")

    selected_topic, video_type, sub_range, sort_by = render_common_filters()
    
    channel_keyword = st.text_input("🔍 키워드로 검색 (선택사항)", placeholder="특정 키워드가 포함된 채널 검색")

    if st.button("🏆 황금채널 탐색 시작"):
        if not api_key:
            st.error("⚠️ 좌측 사이드바에 비밀번호를 먼저 입력해 주세요.")
        else:
            try:
                youtube = build("youtube", "v3", developerKey=api_key)
                with st.spinner("🏆 카테고리별 황금 채널을 분석하는 중입니다..."):
                    search_q = channel_keyword if channel_keyword else (selected_topic if selected_topic != "전체" else "인기")
                    
                    search_response = youtube.search().list(
                        q=search_q,
                        part="id,snippet",
                        maxResults=30,
                        type="channel"
                    ).execute()

                    ch_ids = [item["id"]["channelId"] for item in search_response.get("items", [])]

                    if ch_ids:
                        channels_response = youtube.channels().list(
                            part="snippet,statistics",
                            id=",".join(ch_ids)
                        ).execute()

                        ch_data = []
                        for ch in channels_response.get("items", []):
                            snippet = ch["snippet"]
                            stats = ch["statistics"]
                            
                            subs = int(stats.get("subscriberCount", 0))
                            views = int(stats.get("viewCount", 0))
                            videos = int(stats.get("videoCount", 0))

                            # 구독자 구간 필터링
                            if sub_range == "0~1만 명 (급성장)" and subs > 10000: continue
                            elif sub_range == "1만~5만 명" and not (10000 <= subs <= 50000): continue
                            elif sub_range == "5만~10만 명" and not (50000 <= subs <= 100000): continue

                            ch_data.append({
                                "채널명": snippet["title"],
                                "구독자수": subs,
                                "총조회수": views,
                                "영상수": videos,
                                "설명": snippet.get("description", "")[:100] + "...",
                                "채널URL": f"https://www.youtube.com/channel/{ch['id']}",
                                "썸네일": snippet["thumbnails"]["default"]["url"]
                            })

                        if ch_data:
                            df_ch = pd.DataFrame(ch_data)
                            if sort_by == "구독자 많은 순":
                                df_ch = df_ch.sort_values(by="구독자수", ascending=False)
                            else:
                                df_ch = df_ch.sort_values(by="총조회수", ascending=False)

                            st.markdown(f"### 🎉 발견된 황금채널 **{len(df_ch)}**개")
                            for idx, row in df_ch.iterrows():
                                col1, col2 = st.columns([1, 4])
                                with col1:
                                    st.image(row["썸네일"], width=80)
                                with col2:
                                    st.markdown(f"### [{row['채널명']}]({row['채널URL']})")
                                    st.write(f"👤 구독자: **{row['구독자수']:,}명** | 👁️ 총 조회수: **{row['총조회수']:,}회** | 📹 동영상: **{row['영상수']:,}개**")
                                    st.caption(row["설명"])
                                st.divider()
                        else:
                            st.warning("조건에 맞는 채널을 찾지 못했습니다.")
                    else:
                        st.warning("채널 검색 결과가 없습니다.")
            except Exception as e:
                st.error(f"오류 발생: {e}")


# ==========================================
# 3. 터진영상
# ==========================================
elif menu == "🔥 터진영상":
    st.subheader("🔥 터진 영상 발굴기")
    st.caption("최근 급상승한 조회수 유행 영상 및 바이럴 콘텐츠를 모아서 확인합니다.")

    selected_topic, video_type, sub_range, sort_by = render_common_filters()

    if st.button("🔥 터진 영상 찾아보기"):
        if not api_key:
            st.error("⚠️ 좌측 사이드바에 비밀번호를 먼저 입력해 주세요.")
        else:
            try:
                youtube = build("youtube", "v3", developerKey=api_key)
                with st.spinner("🔥 급상승 및 조회수 폭발 영상들을 수집하는 중..."):
                    q_str = selected_topic if selected_topic != "전체" else "떡상"
                    duration_param = "short" if video_type == "쇼츠" else ("long" if video_type == "롱폼" else "any")

                    search_response = youtube.search().list(
                        q=q_str,
                        part="id,snippet",
                        maxResults=24,
                        type="video",
                        videoDuration=duration_param,
                        order="viewCount"
                    ).execute()

                    v_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]

                    if v_ids:
                        videos_response = youtube.videos().list(
                            part="snippet,statistics",
                            id=",".join(v_ids)
                        ).execute()

                        v_list = []
                        for item in videos_response.get("items", []):
                            snippet = item["snippet"]
                            stats = item.get("statistics", {})
                            
                            v_list.append({
                                "제목": snippet["title"],
                                "채널명": snippet["channelTitle"],
                                "조회수": int(stats.get("viewCount", 0)),
                                "좋아요": int(stats.get("likeCount", 0)),
                                "URL": f"https://www.youtube.com/watch?v={item['id']}",
                                "썸네일": snippet["thumbnails"]["high"]["url"]
                            })

                        df_v = pd.DataFrame(v_list)
                        st.markdown(f"### 🔥 터진 영상 **{len(df_v)}**개")

                        cols_per_row = 3
                        for i in range(0, len(df_v), cols_per_row):
                            cols = st.columns(cols_per_row)
                            for j in range(cols_per_row):
                                idx = i + j
                                if idx < len(df_v):
                                    row = df_v.iloc[idx]
                                    with cols[j]:
                                        st.image(row["썸네일"], use_container_width=True)
                                        st.markdown(f"**[{row['제목']}]({row['URL']})**")
                                        st.caption(f"📺 {row['채널명']}")
                                        st.write(f"🔥 조회수: **{row['조회수']:,}회** | ❤️ 좋아요: **{row['좋아요']:,}개**")
                    else:
                        st.warning("터진 영상을 찾을 수 없습니다.")
            except Exception as e:
                st.error(f"오류 발생: {e}")
