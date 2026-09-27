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

st.title("⚡ Zutem Finder | 떡상 쇼츠 발굴기")
st.caption("유튜브 알고리즘을 분석하여 빠른 속도로 성장하는 떡상 쇼츠를 검색·비교합니다.")

# 사이드바 설정
with st.sidebar:
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
    st.caption("키워드를 검색하고 조건별 필터를 지정하면 AMS 지수(알고리즘 상승 지수)가 계산됩니다.")

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

# 검색창
keyword = st.text_input("🔍 검색 키워드", placeholder="예: 연예인추천템, 코스트코 추천, 꿀템")

# 세부 필터링 옵션 (골든파인더와 동일한 4대 필터)
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
        st.error("⚠️ 좌측 사이드바에 YouTube Data API 키를 먼저 입력해 주세요!")
    else:
        try:
            youtube = build("youtube", "v3", developerKey=api_key)
            
            with st.spinner("🔍 조건에 부합하는 쇼츠 데이터를 분석 중입니다..."):
                # 날짜 필터 파싱
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

                # 1. API 검색 수행
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
                    # 2. 영상 상세 수집
                    videos_response = youtube.videos().list(
                        part="snippet,statistics",
                        id=",".join(video_ids)
                    ).execute()

                    # 3. 채널 구독자 수 수집
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

                    # 4. 필터링 및 데이터 가공
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

                        # 구독자 수 필터 적용
                        if max_subs_option == "1만 명 이하" and subscribers > 10000: continue
                        elif max_subs_option == "5만 명 이하" and subscribers > 50000: continue
                        elif max_subs_option == "10만 명 이하" and subscribers > 100000: continue
                        elif max_subs_option == "50만 명 이하" and subscribers > 500000: continue

                        # 조회수 범위 필터 적용
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
                        st.warning("지정한 필터 조건(구독자 수/조회수)을 만족하는 쇼츠가 없습니다. 필터를 완화해 보세요.")
                    else:
                        df = pd.DataFrame(data_list)

                        # 정렬 처리
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

                        # 카드형 리스트 레이아웃
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
