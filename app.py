import streamlit as st
import pandas as pd
import requests
import re

# 1. 알라딘 API 키 설정
TTB_KEY = "ttbhos5475221314001" 

# 2. KDC 분류번호별 상세 주제 매핑 (사서님 요청대로 두 자리 중심 확장)
KDC_TOPICS = {
    # 000 총류
    '00': '총류/지식', '04': '컴퓨터/IT/소프트웨어', '07': '신문/언론',
    # 100 철학
    '1': '철학/사상', '18': '심리학/마음', '19': '윤리/도덕',
    # 200 종교
    '2': '종교/신앙',
    # 300 사회과학
    '3': '사회과학', '32': '경제/경영/재테크/비즈니스', '33': '사회학/사회문제', 
    '35': '행정/공공', '36': '법률/법학', '37': '교육', '38': '풍속/민속',
    # 400 자연과학
    '4': '자연과학/과학', '41': '수학', '44': '화학', '47': '생물학/생명',
    # 500 기술과학
    '5': '기술과학/공학', '51': '의학/건강', '53': '농업/원예', 
    '59': '생활과학/요리/육아/가전',
    # 600 예술
    '6': '예술/미술/음악', '63': '공연/연극/영화', '67': '운동/스포츠/레저', '69': '만화',
    # 700 언어
    '7': '언어/어학/외국어', '71': '한국어', '74': '영어',
    # 800 문학 (가장 대출이 많은 구간)
    '8': '문학/글쓰기', '81': '한국문학/소설/시/수필', '82': '중국문학', 
    '84': '영미문학/영어소설', '86': '프랑스문학', '89': '기타문학',
    # 900 역사
    '9': '역사/지리/여행', '91': '한국역사/국사', '98': '지리/여행/관광'
}

st.set_page_config(page_title="단봉늘봄도서관 리브로봇", layout="wide")

# --- 🌿 디자인 설정 (공백 파괴 버전) ---
st.markdown("""
    <style>
    /* 1. 최상단 마진 및 패딩 강제 제거 */
    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
    .stApp { background-color: #f5f5f0; }
    header { visibility: hidden; } /* 스트림릿 상단 바 숨김 */
    
    .main-title { color: #3d3d3d; font-size: 2.5rem; font-weight: 800; text-align: center; margin: 0; }
    .first-reader-badge {
        background-color: #fff3e0; color: #e65100; padding: 4px 10px;
        border-radius: 12px; font-size: 0.8rem; font-weight: 700; border: 1px solid #ffb74d;
    }
    .book-card {
        background-color: white; border-radius: 15px; padding: 15px; 
        margin-bottom: 15px; border: 1px solid #e0e0e0; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .call-number-box {
        background-color: #e8f5e9; color: #2e7d32; padding: 5px 10px;
        border-radius: 5px; font-weight: 800; border: 1px dashed #2e7d32;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>🤖 리브로봇 Lib-Robot</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#5d4037; margin-bottom:20px;'>✨ 단봉늘봄의 '첫 번째 독자'를 기다리는 보물들</p>", unsafe_allow_html=True)

# --- 🛠️ 함수 정의 ---
def get_aladin_data(isbn):
    if not isbn or len(str(isbn)) < 10: return None
    url = f"http://www.aladin.co.kr/ttb/api/ItemLookUp.aspx?ttbkey={TTB_KEY}&itemIdType=ISBN13&ItemId={isbn}&output=js&Version=20131101"
    try:
        res = requests.get(url, timeout=1.5)
        if res.status_code == 200:
            item = res.json().get('item', [])
            if item:
                if 'cover' in item[0]: item[0]['cover'] = item[0]['cover'].replace('coversum', 'cover500')
                return item[0]
    except: return None
    return None

def get_topic(call_num):
    nums = re.findall(r'\d+', str(call_num))
    if nums:
        code = nums[0]
        if code[:2] in KDC_TOPICS: return KDC_TOPICS[code[:2]]
        if code[0] in KDC_MAJOR: return KDC_MAJOR[code[0]]
    return ""

@st.cache_data
def load_data():
    try:
        df = pd.read_csv('unlent.csv', encoding='cp949')
        df.columns = [c.strip() for c in df.columns]
        return df
    except: return None

# --- 🚀 메인 실행 ---
df = load_data()
if df is not None:
    query = st.text_input("🔍 검색어를 입력하세요 (예: 경제, 육아, 소설)", key="search")
    
    if query:
        # 서명 검색 + KDC 주제 검색
        results = df[df['서명'].str.contains(query, na=False) | 
                    df['청구기호'].apply(lambda x: query in get_topic(x))].head(8)

        if not results.empty:
            for i in range(0, len(results), 2):
                cols = st.columns(2)
                for j in range(2):
                    if i + j < len(results):
                        row = results.iloc[i + j]
                        with cols[j]:
                            info = get_aladin_data(row.get('ISBN'))
                            st.markdown("<div class='book-card'>", unsafe_allow_html=True)
                            st.markdown("<span class='first-reader-badge'>💎 첫 번째 대출자 도전!</span>", unsafe_allow_html=True)
                            
                            if info and info.get('cover'):
                                c1, c2 = st.columns([1, 2])
                                with c1: st.image(info['cover'])
                                with c2:
                                    st.subheader(row['서명'])
                                    st.markdown(f"<div class='call-number-box'>📍 {row['청구기호']}</div>", unsafe_allow_html=True)
                                    st.link_button("상세보기", info['link'])
                            else: # 이미지가 없을 경우 레이아웃 간소화
                                st.subheader(row['서명'])
                                st.write(f"저자: {row['저자']}")
                                st.markdown(f"<div class='call-number-box'>📍 {row['청구기호']}</div>", unsafe_allow_html=True)
                            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("🤖 보물을 찾지 못했습니다.")

# --- 📊 설문조사 ---
st.divider()
st.link_button("📊 만족도 설문 참여하기", "https://docs.google.com/forms/d/e/1FAIpQLSe6HrIbXcKPCg99b0gPTlfy-59A-WDb9O3pVoPZRVxpGA3msg/viewform?usp=dialog")
