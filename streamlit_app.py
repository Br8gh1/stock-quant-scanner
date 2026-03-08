import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- 1. Page Config & Neon CSS ---
st.set_page_config(page_title="Alpha Neon Pro", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    /* Main Background & Text */
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    
    /* Neon Blue Card */
    div[data-testid="stMetric"] {
        background-color: #161B22;
        border: 1px solid #00D4FF;
        border-radius: 10px;
        padding: 10px;
        box-shadow: 0 0 5px #00D4FF;
    }
    
    /* Neon Button */
    .stButton>button {
        background-color: transparent;
        color: #00D4FF;
        border: 2px solid #00D4FF;
        border-radius: 20px;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #00D4FF;
        color: black;
        box-shadow: 0 0 15px #00D4FF;
    }
    
    /* Signal Badge Neon */
    .signal-badge {
        background-color: #003366;
        color: #00D4FF;
        border: 1px solid #00D4FF;
        padding: 1px 8px;
        border-radius: 5px;
        font-size: 0.7rem;
        font-weight: bold;
        margin-right: 4px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Data Loading (Same logic) ---
@st.cache_data(ttl=300)
def load_data():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_info = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    client = gspread.authorize(creds)
    sh = client.open("Stock_Scan_Result")
    worksheet = sh.worksheet("Data_Scan")
    return pd.DataFrame(worksheet.get_all_records())

# --- 3. Compact Card Component ---
def render_compact_card(row, idx):
    with st.container():
        # การจัดวางในกรอบเล็ก
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown(f"**{row['name']}**")
        with c2:
            st.markdown(f"<span style='color:#00D4FF'>{row['change']}%</span>", unsafe_allow_html=True)
        
        # Signals แบบย่อ
        signals = row['signals'].split("; ")
        badge_html = "".join([f'<span class="signal-badge">{s[:4]}..</span>' for s in signals])
        st.markdown(badge_html, unsafe_allow_html=True)
        
        # Metrics แบบกระชับ
        col_m1, col_m2 = st.columns(2)
        col_m1.caption(f"Entry: ${row['entry']}")
        col_m2.caption(f"SL: ${row['sl_5%']}")
        
        if st.button("VIEW", key=f"v_{idx}", use_container_width=True):
            st.session_state['selected_stock'] = row['name']
        st.markdown("<hr style='margin:10px 0; border-color:#161B22'>", unsafe_allow_html=True)

# --- 4. Main Layout (Left: List, Right: Chart) ---
try:
    df = load_data()
    
    # แบ่งหน้าจอเป็น 2 ฝั่ง (25% สำหรับรายการหุ้น, 75% สำหรับกราฟ)
    col_list, col_chart = st.columns([1, 3])

    with col_list:
        st.markdown("### ⚡ **LIST**")
        tab1, tab2 = st.tabs(["MOM", "PB"])
        
        with tab1:
            df_m = df[df['signals'].str.contains("TREND", na=False)]
            for i, (_, row) in enumerate(df_m.iterrows()):
                render_compact_card(row, f"m_{i}")
                
        with tab2:
            df_p = df[df['signals'].str.contains("PULLBACK", na=False)]
            for i, (_, row) in enumerate(df_p.iterrows()):
                render_compact_card(row, f"p_{i}")

    with col_chart:
        # เลือกหุ้นตัวแรกเป็น Default ถ้ายังไม่ได้กดเลือก
        target = st.session_state.get('selected_stock', df['name'].iloc[0] if not df.empty else None)
        
        if target:
            # รายละเอียดหุ้นตัวที่เลือก (Target Info)
            stock_data = df[df['name'] == target].iloc[0]
            st.markdown(f"## 🛠 {target} <span style='font-size: 1rem; color: #888;'>| Target 10% Strategy</span>", unsafe_allow_html=True)
            
            # สรุปเป้าหมายด้านบนกราฟ
            t1, t2, t3, t4 = st.columns(4)
            t1.metric("TP1 (10%)", f"${stock_data['tp1_10%']}")
            t2.metric("TP2 (20%)", f"${stock_data['tp2_20%']}")
            t3.metric("TP3 (30%)", f"${stock_data['tp3_30%']}")
            t4.metric("STOP (5%)", f"${stock_data['sl_5%']}", delta="-5%", delta_color="inverse")

            # กราฟ TradingView
            tv_url = f"https://s.tradingview.com/widgetembed/?symbol={target}&interval=D&theme=dark"
            st.components.v1.html(f'<iframe src="{tv_url}" width="100%" height="650" frameborder="0"></iframe>', height=660)
        else:
            st.info("Select a stock from the left to view technical chart.")

except Exception as e:
    st.error(f"Waiting for data... ({e})")
