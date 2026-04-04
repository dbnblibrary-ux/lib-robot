import streamlit as st
import pandas as pd
import requests

# 1. 알라딘 API 키 설정
TTB_KEY = "ttbhos5475221314001" 

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

def get_aladin_data(isbn):
    if not isbn or str(isbn).lower() == 'nan' or len(str(isbn)) < 10: return None
    url = f"http://www.aladin.co.kr/ttb/api/ItemLookUp.aspx?ttbkey={TTB_KEY}&itemIdType=ISBN13&ItemId={isbn}&output=js&Version=20131101"
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            data = response.json()
            if 'item' in data and len(data['item']) > 0:
                item = data['item'][0]
                # 고화질 이미지 처리
                if 'cover' in item:
                    item['cover'] = item['cover'].replace('coversum', 'cover500')
                return item
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
    user_query = st.text_input("🔍 리브로봇에게 검색어를 알려주세요", placeholder="예: 고양이, 힐링, 재테크")

    if user_query:
        stopwords = ["리브로봇", "찾아줘", "추천해줘", "보여줘", "있니", "있
