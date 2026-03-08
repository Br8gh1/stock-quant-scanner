import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- 1. Page Config ---
st.set_page_config(page_title="Alpha Neon Terminal", page_icon="⚡", layout="wide")

# --- 2. CSS: ย้าย Sidebar ไปขวา และล็อคตำแหน่ง ---
st.markdown("""
    <style>
    /* ย้าย Sidebar ไปขวา */
    [data-testid="stSidebar"] {
        left: auto;
        right: 0;
        width: 380px !important;
        background-color: #0E1117;
        border-left: 2px solid #00D4FF;
    }
    
    /* เว้นที่ให้ Sidebar ขวาในหน้าหลัก */
    [data-testid="stAppViewContainer"] {
        padding-right: 380px;
    }

    .stApp { background-color: #0E1117; color: #E0E0E0; }

    /* ตกแต่ง Card หุ้น Neon Style */
    .stock-card {
        background-color: #161B22;
        border-right: 4px solid #00D4FF;
        border-radius: 5px;
        padding: 12px;
        margin-bottom: 10px;
        transition: 0.2s;
    }
    .stock-card:hover {
        background-color: #1E2530;
        box-shadow: 0 0 10px rgba(0, 212, 255, 0.2);
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
    st.info("⚡ Waiting for data sync from Google Sheets...")
else:
    # --- ส่วนที่ 1: Sidebar ฝั่งขวา (Scrollable & Filterable) ---
    with st.sidebar:
        st.markdown("### ⚡ **LIST SCANNER**")
        
        # ฟังก์ชัน Filter แยกกลุ่ม Signal
        filter_type = st.radio("Filter By Signal:", ["All Stocks", "Trend Starter", "Quality Pullback"], horizontal=True)
        st.divider()

        # กรองข้อมูลตามที่เลือก
        if filter_type == "Trend Starter":
            display_df = df[df['signals'].str.contains("TREND", na=False)]
        elif filter_type == "Quality Pullback":
            display_df = df[df['signals'].str.contains("PULLBACK", na=False)]
        else:
            display_df = df

        if display_df.empty:
            st.warning("No stocks found for this signal.")
        else:
            # วนลูปแสดงหุ้นใน Sidebar
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
                
                if st.button(f"ANALYZE {row['name']}", key=f"side_btn_{i}", use_container_width=True):
                    st.session_state['selected_stock'] = row['name']
                st.write("")

    # --- ส่วนที่ 2: หน้าจอหลักฝั่งซ้าย (Fixed Graph & Metrics) ---
    selected = st.session_state.get('selected_stock', df['name'].iloc[0])
    stock_info = df[df['name'] == selected].iloc[0]

    # Header & Metrics Row
    st.markdown(f"## 🛠 {selected} <span style='font-size:1.2rem; color:#00D4FF;'>| Strategy: Target 10%</span>", unsafe_allow_html=True)
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("TP1 (10%)", f"${stock_info['tp1_10%']}")
    m2.metric("TP2 (20%)", f"${stock_info['tp2_20%']}")
    m3.metric("TP3 (30%)", f"${stock_info['tp3_30%']}")
    m4.metric("STOP (5%)", f"${stock_info['sl_5%']}", delta="-5.0%", delta_color="inverse")

    # ส่วนแสดงกราฟ TradingView (ขนาดใหญ่)
    tv_url = f"https://s.tradingview.com/widgetembed/?symbol={selected}&interval=D&theme=dark&style=1&timezone=Etc%2FUTC"
    st.components.v1.html(
        f'<iframe src="{tv_url}" width="100%" height="650" frameborder="0" style="border: 1px solid #1f2937; border-radius: 8px;"></iframe>', 
        height=660
    )
