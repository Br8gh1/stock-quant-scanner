import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- 1. Page Config ---
st.set_page_config(page_title="Alpha Neon Terminal", page_icon="⚡", layout="wide")

# --- 2. CSS เพื่อย้าย Sidebar ไปไว้ฝั่งขวา และปรับแต่งสี Neon ---
st.markdown("""
    <style>
    /* ย้าย Sidebar ไปไว้ฝั่งขวา */
    [data-testid="stSidebar"] {
        left: auto;
        right: 0;
        width: 350px !important;
        background-color: #0E1117;
        border-left: 1px solid #00D4FF;
    }
    
    /* ปรับแต่งพื้นที่หลักให้เต็มจอ (เผื่อที่ให้ Sidebar ขวา) */
    [data-testid="stAppViewContainer"] {
        padding-right: 350px;
    }

    .stApp { background-color: #0E1117; color: #E0E0E0; }

    /* ตกแต่ง Card หุ้น */
    .stock-card {
        background-color: #161B22;
        border-right: 3px solid #00D4FF;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 5px;
    }
    .signal-badge {
        color: #00D4FF;
        border: 1px solid #00D4FF;
        padding: 0px 5px;
        border-radius: 3px;
        font-size: 0.65rem;
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
    except Exception as e:
        return pd.DataFrame()

# --- 4. Main Execution ---
df = load_data()

if df.empty:
    st.info("⚡ System initialized. Awaiting data from Google Sheets...")
else:
    # --- ส่วนที่ 1: รายชื่อหุ้น (Sidebar ฝั่งขวา - เลื่อนได้อิสระ) ---
    with st.sidebar:
        st.markdown("### ⚡ **SCANNER LIST**")
        st.caption("Select a stock to view analysis")
        
        # แสดงรายการหุ้นใน Sidebar
        for i, (_, row) in enumerate(df.iterrows()):
            st.markdown(f"""
                <div class="stock-card">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-weight: bold;">{row['name']}</span>
                        <span style="color: #00D4FF;">{row['change']}%</span>
                    </div>
                    <div style="margin-top: 3px;">
                        {" ".join([f'<span class="signal-badge">{s}</span>' for s in row['signals'].split("; ")])}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if st.button(f"VIEW {row['name']}", key=f"side_{i}", use_container_width=True):
                st.session_state['selected_stock'] = row['name']
            st.write("")

    # --- ส่วนที่ 2: กราฟ (Main Area ฝั่งซ้าย - นิ่งสนิท) ---
    selected = st.session_state.get('selected_stock', df['name'].iloc[0])
    stock_info = df[df['name'] == selected].iloc[0]

    # Header & Metrics
    st.markdown(f"## 🛠 {selected} <span style='font-size:1.2rem; color:#00D4FF;'>| Target 10% Strategy</span>", unsafe_allow_html=True)
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("TP1 (10%)", f"${stock_info['tp1_10%']}")
    m2.metric("TP2 (20%)", f"${stock_info['tp2_20%']}")
    m3.metric("TP3 (30%)", f"${stock_info['tp3_30%']}")
    m4.metric("STOP (5%)", f"${stock_info['sl_5%']}", delta="-5%", delta_color="inverse")

    # TradingView Chart
    # ปรับความสูงให้เต็มหน้าจอ
    tv_url = f"https://s.tradingview.com/widgetembed/?symbol={selected}&interval=D&theme=dark"
    st.components.v1.html(
        f'<iframe src="{tv_url}" width="100%" height="650" frameborder="0" style="border: 1px solid #1f2937; border-radius: 8px;"></iframe>', 
        height=660
    )
