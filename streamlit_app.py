import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- 1. Page Config ---
st.set_page_config(page_title="Alpha Neon Terminal", page_icon="⚡", layout="wide")

# --- 2. CSS: จัดการ Layout และ Fix ส่วน Filter ใน Sidebar ---
st.markdown("""
    <style>
    /* 1. ย้าย Sidebar ไปขวา และตั้งค่าสี */
    [data-testid="stSidebar"] {
        left: auto;
        right: 0;
        width: 380px !important;
        background-color: #0E1117;
        border-left: 2px solid #00D4FF;
    }
    
    /* 2. เว้นพื้นที่หน้าหลักให้ Sidebar ขวา */
    [data-testid="stAppViewContainer"] {
        padding-right: 380px;
    }

    /* 3. ทำให้ Filter ใน Sidebar ถูก Freeze (Sticky) */
    [data-testid="stSidebarUserContent"] {
        padding-top: 1rem;
    }
    
    .sticky-filter {
        position: sticky;
        top: 0;
        background-color: #0E1117;
        z-index: 999;
        padding-bottom: 15px;
        border-bottom: 1px solid #1f2937;
        margin-bottom: 15px;
    }

    .stApp { background-color: #0E1117; color: #E0E0E0; }

    /* 4. ตกแต่ง Card หุ้น */
    .stock-card {
        background-color: #161B22;
        border-right: 4px solid #00D4FF;
        border-radius: 5px;
        padding: 12px;
        margin-bottom: 10px;
    }
    .signal-badge {
        color: #00D4FF;
        border: 1px solid #00D4FF;
        padding: 1px 6px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. Data Loading ---
@st.cache_data(ttl=300)
def load_data():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds_info = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        client = gspread.authorize(creds)
        sh = client.open("Stock_Scan_Result")
        worksheet = sh.worksheet("Data_Scan")
        return pd.DataFrame(worksheet.get_all_records())
    except:
        return pd.DataFrame()

# --- 4. Main Execution ---
df = load_data()

if df.empty:
    st.info("⚡ กำลังรอข้อมูลจากระบบสแกนหุ้น...")
else:
    # --- ส่วนที่ 1: Sidebar ฝั่งขวา (Fixed Filter + Scrollable List) ---
    with st.sidebar:
        # ใช้ container ครอบส่วน Filter เพื่อทำ Sticky ผ่าน CSS (ในที่นี้ใช้ Markdown จำลองส่วนหัว)
        st.markdown('<div class="sticky-filter">', unsafe_allow_html=True)
        st.markdown("### ⚡ **LIST SCANNER**")
        filter_type = st.radio("Signal Filter:", ["All", "Trend", "Pullback"], horizontal=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Logic การกรองข้อมูล
        if filter_type == "Trend":
            display_df = df[df['signals'].str.contains("TREND", na=False)]
        elif filter_type == "Pullback":
            display_df = df[df['signals'].str.contains("PULLBACK", na=False)]
        else:
            display_df = df

        # แสดงรายการหุ้น
        for i, (_, row) in enumerate(display_df.iterrows()):
            st.markdown(f"""
                <div class="stock-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: bold; font-size: 1.1rem;">{row['name']}</span>
                        <span style="color: #00D4FF; font-weight: bold;">{row['change']}%</span>
                    </div>
                    <div style="margin: 6px 0;">
                        {" ".join([f'<span class="signal-badge">{s}</span>' for s in row['signals'].split("; ")])}
                    </div>
                    <div style="font-size: 0.8rem; color: #888;">
                        Entry: ${row['entry']} | SL: ${row['sl_5%']}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"VIEW {row['name']}", key=f"side_btn_{i}", use_container_width=True):
                st.session_state['selected_stock'] = row['name']
            st.write("")

    # --- ส่วนที่ 2: หน้าจอหลักฝั่งซ้าย (Fixed Graph) ---
    selected = st.session_state.get('selected_stock', df['name'].iloc[0])
    stock_info = df[df['name'] == selected].iloc[0]

    # Header & Metrics
    st.markdown(f"## 🛠 {selected} <span style='font-size:1.2rem; color:#00D4FF;'>| TP 10% Strategy</span>", unsafe_allow_html=True)
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("TP1 (10%)", f"${stock_info['tp1_10%']}")
    m2.metric("TP2 (20%)", f"${stock_info['tp2_20%']}")
    m3.metric("TP3 (30%)", f"${stock_info['tp3_30%']}")
    m4.metric("STOP (5%)", f"${stock_info['sl_5%']}", delta="-5.0%", delta_color="inverse")

    # กราฟ TradingView
    tv_url = f"https://s.tradingview.com/widgetembed/?symbol={selected}&interval=D&theme=dark&style=1"
    st.components.v1.html(
        f'<iframe src="{tv_url}" width="100%" height="650" frameborder="0" style="border: 1px solid #1f2937; border-radius: 8px;"></iframe>', 
        height=660
    )
