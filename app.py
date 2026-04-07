import streamlit as st
import pandas as pd
import requests
import re

# 1. 알라딘 API 키 설정
TTB_KEY = "ttbhos5475221314001" 

# 2. KDC 상세 주제 매핑 (두 자리 중심)
KDC_TOPICS = {
    '00': '총류/지식', '04': '컴퓨터/IT/정보학/프로그래밍', '07': '신문/언론/잡지',
    '10': '철학/사상', '18': '심리학/마음/상담', '19': '윤리/도덕',
    '20': '종교/신앙',
    '30': '사회과학', '32': '경제/경영/재테크/비즈니스/돈/주식', '33': '사회학/사회문제', 
    '35': '행정/공공', '36': '법률/법학', '37': '교육/학교', '38': '풍속/민속',
    '40': '자연과학/과학', '41': '수학', '44': '화학', '47': '생물학/생명',
    '50': '기술과학/공학', '51': '의학/건강/질병', '53': '농업/원예', 
    '59': '생활과학/요리/육아/살림/가전',
    '60': '예술/미술/음악', '63': '공연/연극/영화', '67': '운동/스포츠/레저', '69': '만화',
    '70': '언어/어학/외국어', '71': '한국어', '74': '영어',
    '80': '문학/글쓰기', '81': '한국문학/한국소설/시/수필/에세이', '82': '중국문학', 
    '84': '영미문학/영어소설', '86': '프랑스문학', '89': '기타문학',
    '90': '역사/지리/여행', '91': '한국역사/국사', '98': '지리/여행/관광'
}

# 3. 페이지 설정
st.set_page_config(page_title="단봉늘봄도서관 리브로봇", layout="wide")

# --- 🌿 디자인 설정 (사서님이 좋아하신 스타일 + 상단 공백 제거) ---
st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    header { visibility: hidden; }
    .stApp { background-color: #f5f5f0; }
    .main-title { color: #3d3d3d; font-size: 2.8rem; font-weight: 800; text-align: center; margin-top: 0px; }
    .first-reader-badge {
        background-color: #fff3e0; color: #e65100; padding: 4px 10px;
        border-radius: 12px; font-size: 0.8rem; font-weight: 700;
        border: 1px solid #ffb74d; display: inline-block; margin-bottom: 8px;
    }
    .book-card {
        background-color: rgba(255, 255, 255, 0.7); border-radius: 15px;
        padding: 20px; margin-bottom: 20px; border: 1px solid rgba(0,0,0,0.08);
        min-height: 400px;
    }
    .call-number-box {
        background-color: #e8f5e9; color: #2e7d32; padding: 8px 12px;
        border-radius: 8px; font-weight: 800; font-size: 1.1rem;
        margin: 10px 0; display: inline-block; border: 1px dashed #2e7d32;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>🤖 리브로봇 Lib-Robot</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align:center; color:#5d4037;'>✨ 단봉늘봄의 '첫 번째 독자'를 기다리는 보물들</h4>", unsafe_allow_html=True)

# --- 🛠️ 함수 정의 ---
def get_aladin_data(isbn):
    if not isbn or len(str(isbn)) < 10: return None
    url = f"http://www.aladin.co.kr/ttb/api/ItemLookUp.aspx?ttbkey={TTB_KEY}&itemIdType=ISBN13&ItemId={isbn}&output=js&Version=20131101"
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            data = response.json()
            if 'item' in data and len(data['item']) > 0:
                item = data['item'][0]
                if 'cover' in item:
                    item['cover'] = item['cover'].replace('coversum', 'cover500')
                return item
    except: return None
    return None

def get_topic_from_call_number(call_number):
    if not call_number or pd.isna(call_number): return ""
    nums = re.findall(r'\d+', str(call_number))
    if nums:
        code = nums[0]
        if len(code) >= 2 and code[:2] in KDC_TOPICS: return KDC_TOPICS[code[:2]]
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
    st.write("---")
    user_query = st.text_input("🔍 리브로봇에게 검색어를 알려주세요", placeholder="예: 경제, 육아, 소설, 힐링")

    if user_query:
        stopwords = ["리브로봇", "찾아줘", "추천해줘", "보여줘", "있니", "있어"]
        cleaned_query = user_query
        for word in stopwords: cleaned_query = cleaned_query.replace(word, "")
        cleaned_query = cleaned_query.strip()

        if cleaned_query:
            # 서명 검색 + KDC 주제어 매칭
            title_mask = unlent_df['서명'].str.contains(cleaned_query, na=False, case=False)
            def match_topic(row):
                topic = get_topic_from_call_number(row.get('청구기호', ''))
                return cleaned_query in topic if topic else False
            
            topic_mask = unlent_df.apply(match_topic, axis=1)
            results = unlent_df[title_mask | topic_mask].head(8)

            if not results.empty:
                # 사서님이 좋아하신 2열 배치 로직 시작
                for i in range(0, len(results), 2):
                    cols = st.columns(2)
                    for j in range(2):
                        if i + j < len(results):
                            row = results.iloc[i + j]
                            with cols[j]:
                                book_info = get_aladin_data(row.get('ISBN'))
                                if book_info:
                                    st.markdown("<div class='book-card'>", unsafe_allow_html=True)
                                    st.markdown("<span class='first-reader-badge'>💎 당신이 첫 번째 대출자입니다!</span>", unsafe_allow_html=True)
                                    
                                    c1, c2 = st.columns([1, 2])
                                    with c1:
                                        st.image(book_info['cover'], use_container_width=True)
                                    with c2:
                                        st.subheader(row['서명'])
                                        st.write(f"**{row['저자']}** | {row.get('발행자', '출판사 미상')}")
                                        st.markdown(f"<div class='call-number-box'>🏃‍♂️ 이 책 찾으러 가기: {row['청구기호']}</div>", unsafe_allow_html=True)
                                        desc = book_info.get('description', '이 책의 첫 페이지를 여는 주인공이 되어보세요.')
                                        st.markdown(f"<div style='font-size:0.85rem; color:#555;'>{desc[:110]}...</div>", unsafe_allow_html=True)
                                        st.link_button("🍀 책 정보 상세 보기", book_info['link'])
                                    st.markdown("</div>", unsafe_allow_html=True)
                                else:
                                    # 데이터가 없을 때의 깔끔한 카드 (이 부분도 사서님이 좋아하신 구조!)
                                    st.markdown(f"""
                                    <div class='book-card'>
                                        <span class='first-reader-badge'>💎 당신이 첫 번째 대출자입니다!</span>
                                        <h4>{row['서명']}</h4>
                                        <p>{row['저자']}</p>
                                        <div class='call-number-box'>🏃‍♂️ 이 책 찾으러 가기: {row['청구기호']}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
            else:
                st.warning("🤖: 보물을 찾지 못했어요.")

# --- 📊 설문조사 섹션 ---
st.divider() 
st.write("### 🎁 리브로봇 이용 후기 남기기")
st.link_button("만족도 설문 참여", "https://docs.google.com/forms/d/e/1FAIpQLSe6HrIbXcKPCg99b0gPTlfy-59A-WDb9O3pVoPZRVxpGA3msg/viewform?usp=dialog")