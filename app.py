import streamlit as st
import pandas as pd
import requests

# 1. 알라딘 API 키 설정
TTB_KEY = "ttbhos5475221314001" 

st.set_page_config(page_title="단봉늘봄도서관 리브로봇", layout="wide")

# --- 🌿 '첫 번째 독자' 테마 디자인 ---
st.markdown("""
    <style>
    .stApp { background-color: #f5f5f0; }
    .main-title { color: #3d3d3d; font-size: 3rem; font-weight: 800; text-align: center; margin-top: 20px; }
    
    /* 첫 번째 독자 강조 뱃지 */
    .first-reader-badge {
        background-color: #fff3e0;
        color: #e65100;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 700;
        border: 1px solid #ffb74d;
        display: inline-block;
        margin-bottom: 8px;
    }
    
    .book-card {
        background-color: rgba(255, 255, 255, 0.6);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid rgba(0,0,0,0.08);
    }
    
    .call-number-box {
        background-color: #e8f5e9;
        color: #2e7d32;
        padding: 8px 12px;
        border-radius: 8px;
        font-weight: 800;
        font-size: 1.1rem;
        margin: 10px 0;
        display: inline-block;
        border: 1px dashed #2e7d32;
    }
    </style>
    """, unsafe_allow_html=True)

# 헤더 부분에 '첫 번째 독자' 컨셉 명시
st.markdown("<h1 class='main-title'>🤖 리브로봇 Lib-Robot</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align:center; color:#5d4037;'>✨ 단봉늘봄의 '첫 번째 독자'를 기다리는 보물들</h4>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#8d6e63; font-size:0.9rem;'>인기 도서 말고, 아직 아무의 손길도 닿지 않은 소중한 책의 첫 주인이 되어보세요.</p>", unsafe_allow_html=True)

def get_aladin_data(isbn):
    if not isbn or str(isbn).lower() == 'nan' or len(str(isbn)) < 10: return None
    url = f"http://www.aladin.co.kr/ttb/api/ItemLookUp.aspx?ttbkey={TTB_KEY}&itemIdType=ISBN13&ItemId={isbn}&output=js&Version=20131101"
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            data = response.json()
            return data['item'][0] if 'item' in data and len(data['item']) > 0 else None
    except: return None
    return None

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

unlent_df = load_data()

if unlent_df is not None:
    st.write("---")
    user_query = st.text_input("🔍 리브로봇에게 검색어를 알려주세요 (예: 고양이, 힐링, 재테크)", placeholder="단어로 입력하면 더 잘 찾아요!")

    if user_query:
        stopwords = ["리브로봇", "찾아줘", "추천해줘", "보여줘", "있니", "있어"]
        cleaned_query = user_query
        for word in stopwords: cleaned_query = cleaned_query.replace(word, "")
        cleaned_query = cleaned_query.strip()

        if cleaned_query:
            results = unlent_df[unlent_df['서명'].str.contains(cleaned_query, na=False, case=False)].head(8)

            if not results.empty:
                st.info(f"🍀 리브로봇이 서가 깊숙이 숨어있던 **'{cleaned_query}'** 보물들을 찾아냈어요!")
                
                for i in range(0, len(results), 2):
                    cols = st.columns(2)
                    for j in range(2):
                        if i + j < len(results):
                            row = results.iloc[i + j]
                            with cols[j]:
                                book_info = get_aladin_data(row.get('ISBN'))
                                
                                if book_info:
                                    st.markdown("<div class='book-card'>", unsafe_allow_html=True)
                                    # 💎 첫 번째 독자 뱃지 추가
                                    st.markdown("<span class='first-reader-badge'>💎 당신이 첫 번째 대출자입니다!</span>", unsafe_allow_html=True)
                                    
                                    c1, c2 = st.columns([1, 2])
with c1:
    # 이미지가 있을 때, 작은 주소(coversum)를 큰 주소(cover500)로 바꿔서 보여줘!
    high_res_cover = book_info['cover'].replace('coversum', 'cover500')
    st.image(high_res_cover, use_container_width=True)
                                    with c2:
                                        st.subheader(row['서명'])
                                        st.write(f"**{row['저자']}** | {row.get('발행자', '출판사 미상')}")
                                        
                                        # 📍 청구기호 강조
                                        st.markdown(f"<div class='call-number-box'>🏃‍♂️ 이 책 찾으러 가기: {row['청구기호']}</div>", unsafe_allow_html=True)
                                        
                                        desc = book_info.get('description', '이 책의 첫 페이지를 여는 주인공이 되어보세요.')
                                        st.markdown(f"<div style='font-size:0.85rem; color:#555;'>{desc[:95]}...</div>", unsafe_allow_html=True)
                                        
                                        st.link_button("🍀 책 정보 더 보기", book_info['link'])
                                    st.markdown("</div>", unsafe_allow_html=True)
                                else:
                                    # 정보 로딩 실패 시에도 컨셉 유지
                                    st.markdown(f"""
                                    <div class='book-card'>
                                        <span class='first-reader-badge'>💎 당신이 첫 번째 대출자입니다!</span>
                                        <h4>{row['서명']}</h4>
                                        <div class='call-number-box'>🏃‍♂️ 이 책 찾으러 가기: {row['청구기호']}</div>
                                        <p style='font-size:0.8rem; color:#666;'>서가에서 이 책의 첫 주인을 기다리고 있어요.</p>
                                    </div>
                                    """, unsafe_allow_html=True)
            else:
                st.warning("🤖: 보물을 찾지 못했어요. 다른 단어로 검색해 보세요!")
