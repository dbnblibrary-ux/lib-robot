import streamlit as st
import pandas as pd
import requests
import re

# 1. 알라딘 API 키 설정
TTB_KEY = "ttbhos5475221314001" 

# 2. KDC 분류번호별 주제 매핑 (앞 1~2자리 기준 상세화)
KDC_TOPICS = {
    '0': '총류/컴퓨터/정보학', '1': '철학/심리학', '2': '종교', 
    '3': '사회과학', '32': '경제/경영', '33': '사회/정치',
    '4': '자연과학/과학', '5': '기술과학/의학/공학', '6': '예술/취미/스포츠',
    '7': '언어/어학', '8': '문학/소설/시/에세이', '9': '역사/지리/여행'
}

st.set_page_config(page_title="단봉늘봄도서관 리브로봇", layout="wide")

# --- 🌿 디자인 설정 ---
st.markdown("""
    <style>
    .stApp { background-color: #f5f5f0; }
    .main-title { color: #3d3d3d; font-size: 3rem; font-weight: 800; text-align: center; margin-top: 20px; }
    .first-reader-badge {
        background-color: #fff3e0; color: #e65100; padding: 4px 10px;
        border-radius: 12px; font-size: 0.8rem; font-weight: 700;
        border: 1px solid #ffb74d; display: inline-block; margin-bottom: 8px;
    }
    .book-card {
        background-color: rgba(255, 255, 255, 0.6); border-radius: 15px;
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
                if 'cover' in item:
                    item['cover'] = item['cover'].replace('coversum', 'cover500')
                return item
    except: return None
    return None

def get_topic_from_call_number(call_number):
    """청구기호에서 숫자를 추출해 KDC 주제어를 반환"""
    if not call_number or pd.isna(call_number): return ""
    nums = re.findall(r'\d+', str(call_number))
    if nums:
        full_code = nums[0]
        # 32(경제) 같은 세부 분류 우선 확인 후 대분류 확인
        if full_code[:2] in KDC_TOPICS: return KDC_TOPICS[full_code[:2]]
        elif full_code[0] in KDC_TOPICS: return KDC_TOPICS[full_code[0]]
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
    user_query = st.text_input("🔍 리브로봇에게 검색어를 알려주세요", placeholder="예: 경제, 소설, 과학, 심리")

    if user_query:
        stopwords = ["리브로봇", "찾아줘", "추천해줘", "보여줘", "있니", "있어"]
        cleaned_query = user_query
        for word in stopwords: cleaned_query = cleaned_query.replace(word, "")
        cleaned_query = cleaned_query.strip()

        if cleaned_query:
            # 1. 서명 검색 필터
            title_mask = unlent_df['서명'].str.contains(cleaned_query, na=False, case=False)
            
            # 2. 청구기호 기반 주제어 검색 필터 (지능형 연계)
            def match_topic(row):
                topic = get_topic_from_call_number(row.get('청구기호', ''))
                return cleaned_query in topic if topic else False
            
            topic_mask = unlent_df.apply(match_topic, axis=1)
            
            # 3. 결과 합치기
            results = unlent_df[title_mask | topic_mask].head(8)

            if not results.empty:
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
                                    with c1:
                                        st.image(book_info['cover'], use_container_width=True)
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
                st.warning("🤖: 보물을 찾지 못했어요. 다른 검색어를 입력해 보시겠어요?")

# --- 📊 설문조사 섹션 (항상 하단에 노출) ---
st.divider() 
st.write("### 🎁 리브로봇 이용 후기 남기기")
st.write("사서님과 이용자분들의 소중한 한마디가 단봉늘봄도서관을 더 똑똑하게 만듭니다.")
st.link_button("📊 만족도 설문 참여 (10초 소요)", "https://docs.google.com/forms/d/e/1FAIpQLSe6HrIbXcKPCg99b0gPTlfy-59A-WDb9O3pVoPZRVxpGA3msg/viewform?usp=dialog")
