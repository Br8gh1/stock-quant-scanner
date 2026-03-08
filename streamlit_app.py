import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- 1. Page Config ---
st.set_page_config(page_title="Alpha Neon Terminal", page_icon="⚡", layout="wide")

# --- 2. CSS: ล็อคตำแหน่งกราฟและรายการหุ้น ---
st.markdown("""
    <style>
    /* บังคับสีพื้นหลัง */
    .stApp { background-color: #0E1117; color: #E0E0E0; }

    /* ฝั่งซ้าย: ล็อคกราฟให้นิ่ง (Fixed) */
    [data-testid="stColumn"]:nth-child(1) {
        position: fixed;
        width: 65% !important;
        left: 2rem;
        top: 4rem;
        height: 85vh;
        overflow: hidden;
    }

    /* ฝั่งขวา: รายชื่อหุ้นให้เลื่อนได้ (Scroll) */
    [data-testid="stColumn"]:nth-child(2) {
        margin-left: 67% !important; /* เว้นที่ให้ฝั่งซ้าย */
        height: 100vh;
        overflow-y: auto !important;
        padding-right: 15px;
        padding-bottom: 100px;
    }

    /* ตรึง Filter ไว้ด้านบนของรายการหุ้น */
    .sticky-header {
        position: sticky;
        top: 0;
        background-color: #0E1117;
        z-index: 99;
        padding: 10px 0;
        border-bottom: 2px solid #00D4FF;
        margin-bottom: 15px;
    }

    /* ตกแต่ง Card หุ้น */
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

# --- 4. Main Layout ---
df = load_data()

if df.empty:
    st.info("⚡ กำลังเชื่อมต่อข้อมูลจาก Google Sheets...")
else:
    # แบ่ง Column [2.2, 1] กราฟใหญ่กว่ารายการหุ้น
    col_left, col_right = st.columns([2.2, 1])

    # --- ฝั่งซ้าย: กราฟ (ตำแหน่งคงที่) ---
    with col_left:
        selected = st.session_state.get('selected_stock', df['name'].iloc[0])
        stock_info = df[df['name'] == selected].iloc[0]

        # Header ข้อมูลหุ้น
        st.markdown(f"### 🛠 {selected} | <span style='color:#00D4FF'>Target 10% Strategy</span>", unsafe_allow_html=True)
        
        # แสดง Metrics กำไร/ขาดทุน
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("TP1 (10%)", f"${stock_info['tp1_10%']}")
        m2.metric("TP2 (20%)", f"${stock_info['tp2_20%']}")
        m3.metric("TP3 (30%)", f"${stock_info['tp3_30%']}")
        m4.metric("STOP (5%)", f"${stock_info['sl_5%']}", delta="-5.0%", delta_color="inverse")

        # กราฟ TradingView (ระบุความสูงและ IFrame ให้ชัดเจนเพื่อป้องกันการหาย)
        tv_url = f"https://s.tradingview.com/widgetembed/?symbol={selected}&interval=D&theme=dark"
        st.components.v1.html(
            f'<iframe src="{tv_url}" width="100%" height="600" frameborder="0" style="border: 1px solid #1f2937; border-radius: 8px;"></iframe>', 
            height=610
        )

    # --- ฝั่งขวา: รายชื่อหุ้น (เลื่อนได้) ---
    with col_right:
        # ส่วน Filter ที่ถูกล็อคไว้ด้านบน
        st.markdown('<div class="sticky-header">', unsafe_allow_html=True)
        st.markdown("### ⚡ **SCANNER LIST**")
        filter_type = st.radio("Signal Filter:", ["All", "Trend", "Pullback"], horizontal=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Logic กรองหุ้น
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
                        <span style="font-weight: bold; font-size: 1.1rem; color: white;">{row['name']}</span>
                        <span style="color: #00D4FF; font-weight: bold;">{row['change']}%</span>
                    </div>
                    <div style="margin: 6px 0;">
                        {" ".join([f'<span class="signal-badge">{s}</span>' for s in row['signals'].split("; ")])}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"ANALYZE {row['name']}", key=f"btn_{i}", use_container_width=True):
                st.session_state['selected_stock'] = row['name']
                st.rerun()
            st.write("")
