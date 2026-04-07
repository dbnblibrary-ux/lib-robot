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

# --- 🌿 디자인 설정 ---
st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
    .stApp { background-color: #f5f5f0; }
    .main-title { color: #3d3d3d; font-size: 2.8rem; font-weight: 800; text-align: center; margin-top: 0px; margin-bottom: 5px; }
    .first-reader-badge {
        background-color: #fff3e0; color: #e65100; padding: 4px 10px;
        border-radius: 12px; font-size: 0.8rem; font-weight: 700;
        border: 1px solid #ffb74d; display: inline-block; margin-bottom: 8px;
    }
    .book-card {
        background-color: rgba(255, 255, 255, 0.8); border-radius: 15px;
        padding: 20px; margin-bottom: 20px; border: 1px solid rgba(0,0,0,0.08);
        box-shadow: 0 4px 6px rgba(0,0,0,0.02); min-height: 420px;
    }
    .call-number-box {
        background-color: #e8f5e9; color: #2e7d32; padding: 8px 12px;
        border-radius: 8px; font-weight: 800; font-size: 1.1rem;
        margin: 10px 0; display: inline-block; border: 1px dashed #2e7d32;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>🤖 리브로봇 Lib-Robot</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#5d4037; font-size:1.1rem;'>✨ 단봉늘봄의 '첫 번째 독자'를 기다리는 보물들</p>", unsafe_allow_html=True)

# --- 🛠️ 유틸리티 함수 ---
def get_aladin_data(isbn):
    if not isbn or str(isbn).lower() == 'nan' or len(str(isbn)) < 10: return None
    url = f"http://www.aladin.co.kr/ttb/api/ItemLookUp.aspx?ttbkey={TTB_KEY}&itemIdType=ISBN13&ItemId={isbn}&output=js&Version=20131101"
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            data = response.json()
            if 'item' in data and len(data['item']) > 0:
                item = data['item'][0]
                if 'cover' in item: item['cover'] = item['cover'].replace('coversum', 'cover500')
                return item
    except: return None
    return None

def get_topic_from_call_number(call_number):
    if not call_number or pd.isna(call_number): return ""
    nums = re.findall(r'\d+', str(call_number))
    if nums:
        code = nums[0]
        # 1순위: 두 자리(32, 59 등) 매핑 확인
        if len(code) >= 2 and code[:2] in KDC_TOPICS: return KDC_TOPICS[code[:2]]
        # 2순위: 한 자리(8, 3 등) 매핑 확인
        elif code[0] in KDC_TOPICS: return KDC_TOPICS[code[0]]
    return ""

@st.cache_data
def load_data():
    try:
        df = pd.read_csv('unlent.csv', encoding='cp949')
        df.columns = [col.strip() for col in df.columns]
        if 'ISBN' in df.columns:
            df['ISBN'] = df['ISBN'].fillna('').astype(str).apply(lambda x: x.split('.')[0] if '.' in x else x)
            df['ISBN'] = df['ISBN'].str.replace(r'[^0-9X]', '', regex=True)
        return df
    except: return None

# --- 🚀 메인 로직 ---
unlent_df = load_data()

if unlent_df is not None:
    user_query = st.text_input("🔍 리브로봇에게 검색어를 알려주세요", placeholder="예: 경제, 육아, 심리, 소설")

    if user_query:
        stopwords = ["리브로봇", "찾아줘", "추천해줘", "보여줘", "있니", "있어"]
        cleaned_query = user_query
        for word in stopwords: cleaned_query = cleaned_query.replace(word, "")
        cleaned_query = cleaned_query.strip()

        if cleaned_query:
            # 1. 서명 검색
            title_mask = unlent_df['서명'].str.contains(cleaned_query, na=False, case=False)
            
            # 2. 청구기호 기반 주제어 검색 (두 자리 상세 매핑 적용)
            def match_topic(row):
                topic = get_topic_from_call_number(row.get('청구기호', ''))
                # 검색어가 주제어에 포함되는지 확인 (예: '경제' 검색 시 '경제/경영' 주제 매칭)
                return cleaned_query in topic if topic else False
            
            topic_mask = unlent_df.apply(match_topic, axis=1)
            results = unlent_df[title_mask | topic_mask].head(8)

            if not results.empty:
                st.write(f"✅ '{cleaned_query}' 키워드로 발견한 보물들입니다!")
                for i in range(0, len(results), 2):
                    cols = st.columns(2)
                    for j in range(2):
                        if i + j < len(results):
                            row = results.iloc[i + j]
                            with cols[j]:
                                book_info = get_aladin_data(row.get('ISBN'))
                                st.markdown("<div class='book-card'>", unsafe_allow_html=True)
                                st.markdown("<span class='first-reader-badge'>💎 당신이 첫 번째 대출자입니다!</span>", unsafe_allow_html=True)
                                
                                if book_info:
                                    c1, c2 = st.columns([1, 2])
                                    with c1: st.image(book_info['cover'], use_container_width=True)
                                    with c2:
                                        st.subheader(row['서명'])
                                        st.write(f"**{row['저자']}** | {row.get('발행자', '출판사 미상')}")
                                        st.markdown(f"<div class='call-number-box'>🏃‍♂️ 이 책 찾으러 가기: {row['청구기호']}</div>", unsafe_allow_html=True)
                                        desc = book_info.get('description', '이 책의 첫 페이지를 여는 주인공이 되어보세요.')
                                        st.markdown(f"<div style='font-size:0.85rem; color:#555;'>{desc[:95]}...</div>", unsafe_allow_html=True)
                                        st.link_button("🍀 책 정보 상세 보기", book_info['link'])
                                else:
                                    st.subheader(row['서명'])
                                    st.write(f"**{row['저자']}**")
                                    st.markdown(f"<div class='call-number-box'>🏃‍♂️ 이 책 찾으러 가기: {row['청구기호']}</div>", unsafe_allow_html=True)
                                    st.info("상세 정보를 불러올 수 없는 도서입니다.")
                                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.warning("🤖: 보물을 찾지 못했어요. 주제어(예: 경제, 심리)로 다시 검색해 보세요!")

# --- 📊 설문조사 섹션 ---
st.divider() 
st.write("### 🎁 리브로봇 이용 후기 남기기")
st.link_button("📊 만족도 설문 참여", "https://docs.google.com/forms/d/e/1FAIpQLSe6HrIbXcKPCg99b0gPTlfy-59A-WDb9O3pVoPZRVxpGA3msg/viewform?usp=dialog")