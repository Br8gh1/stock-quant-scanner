import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- 1. Page Config ---
st.set_page_config(page_title="Br8gh1", page_icon="⚡", layout="wide")

# --- 2. CSS: บังคับให้หน้าจอแบ่งส่วนชัดเจน ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; overflow: hidden; }

    /* ฝั่งซ้าย: กราฟ (นิ่งสนิท) */
    [data-testid="stColumn"]:nth-child(1) {
        height: 70vh;
        overflow: hidden;
        padding-right: 10px;
    }

    /* ฝั่งขวา: รายชื่อหุ้น (เลื่อนได้) */
    [data-testid="stColumn"]:nth-child(2) {
        height: 95vh;
        overflow-y: auto !important;
        background-color: #0E1117;
        border-left: 1px solid #1f2937;
        padding-left: 20px;
        padding-bottom: 50px;
    }

    /* ปรับแต่งส่วน Filter ให้ Sticky อยู่บนสุดของคอลัมน์ขวา */
    .sticky-header {
        position: sticky;
        top: 0;
        background-color: #0E1117;
        z-index: 999;
        padding: 10px 0;
        border-bottom: 1px solid #00D4FF;
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

# --- 4. Main Layout (แบ่ง 2 ฝั่งชัดเจน) ---
df = load_data()

if df.empty:
    st.info("⚡ กำลังรอข้อมูลจากระบบสแกนหุ้น...")
else:
    # ใช้ Columns ปกติแต่ควบคุมด้วย CSS ด้านบน
    col_graph, col_list = st.columns([2.5, 1])

    # --- ฝั่งซ้าย: กราฟและตัวเลข (ตำแหน่งคงที่) ---
    with col_graph:
        selected = st.session_state.get('selected_stock', df['name'].iloc[0])
        stock_info = df[df['name'] == selected].iloc[0]

        st.markdown(f"## 🛠 {selected} <span style='font-size:1.2rem; color:#00D4FF;'>| TP 10% Strategy</span>", unsafe_allow_html=True)
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("TP1 (10%)", f"${stock_info['tp1_10%']}")
        m2.metric("TP2 (20%)", f"${stock_info['tp2_20%']}")
        m3.metric("TP3 (30%)", f"${stock_info['tp3_30%']}")
        m4.metric("STOP (5%)", f"${stock_info['sl_5%']}", delta="-5.0%", delta_color="inverse")

        # กราฟ TradingView
        tv_url = f"https://s.tradingview.com/widgetembed/?symbol={selected}&interval=D&theme=dark&style=1"
        st.components.v1.html(
            f'<iframe src="{tv_url}" width="100%" height="680" frameborder="0" style="border: 1px solid #1f2937; border-radius: 8px;"></iframe>', 
            height=690
        )

    # --- ฝั่งขวา: รายชื่อหุ้น (เลื่อนได้ และ Filter Freeze อยู่บน) ---
    with col_list:
        # ส่วนหัวและ Filter (จะ Sticky ตาม CSS sticky-header)
        st.markdown('<div class="sticky-header">', unsafe_allow_html=True)
        st.markdown("### ⚡ **SCANNER LIST**")
        filter_type = st.radio("Signal:", ["All", "Trend", "Pullback"], horizontal=True, key="filter_radio")
        st.markdown('</div>', unsafe_allow_html=True)

        # การกรองข้อมูล
        if filter_type == "Trend":
            display_df = df[df['signals'].str.contains("TREND", na=False)]
        elif filter_type == "Pullback":
            display_df = df[df['signals'].str.contains("PULLBACK", na=False)]
        else:
            display_df = df

        # แสดงรายการหุ้นเป็น Card
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
                    <div style="font-size: 0.8rem; color: #888;">
                        In: ${row['entry']} | SL: ${row['sl_5%']}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"ANALYZE {row['name']}", key=f"btn_{i}", use_container_width=True):
                st.session_state['selected_stock'] = row['name']
                st.rerun()
            st.write("")
