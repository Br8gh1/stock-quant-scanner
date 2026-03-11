import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- 1. Page Config ---
st.set_page_config(page_title="Br!gh1 System", page_icon="⚡", layout="wide")

# --- 2. CSS: ปรับแต่ง Layout ให้กราฟอยู่ซ้าย (Fixed) และ List อยู่ขวา (Scroll) ---
st.markdown("""
    <style>
    /* บังคับสีพื้นหลัง */
    .stApp { background-color: #0E1117; color: #E0E0E0; }

    /* ย้าย Sidebar ไปขวาและล็อคความกว้าง */
    [data-testid="stSidebar"] {
        left: auto;
        right: 0;
        width: 400px !important;
        background-color: #0E1117;
        border-left: 2px solid #00D4FF;
    }
    
    /* ปรับพื้นที่หลักให้เต็มจอเพื่อวางกราฟ */
    section[data-testid="stMain"] {
        margin-right: 400px;
    }

    /* ส่วนหัว Filter ใน Sidebar ให้ติดหนึบ (Sticky) */
    .sticky-header {
        position: sticky;
        top: 0;
        background-color: #0E1117;
        z-index: 999;
        padding: 15px 0;
        border-bottom: 1px solid #1f2937;
    }

    /* ตกแต่ง Card หุ้น */
    .stock-card {
        background-color: #161B22;
        border-right: 4px solid #00D4FF;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .signal-badge {
        color: #00D4FF;
        border: 1px solid #00D4FF;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: bold;
    }
    .entry-price {
        color: #FFFFFF;
        font-weight: bold;
        font-size: 1rem;
    }
    .sl-price {
        color: #FF4B4B;
        font-size: 0.9rem;
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
    st.info("⚡ System is active. Waiting for scanner data from Google Sheets...")
else:
    # --- ส่วนที่ 1: Sidebar ฝั่งขวา (Scrollable List with Entry Info) ---
    with st.sidebar:
        # ส่วนหัวและ Filter (Sticky)
        st.markdown('<div class="sticky-header">', unsafe_allow_html=True)
        st.markdown("### ⚡ **Br!gh1 System**")
        filter_type = st.radio("Signal:", ["All", "Trend", "Pullback"], horizontal=True)
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
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                        <span style="font-weight: bold; font-size: 1.2rem; color: white;">{row['name']}</span>
                        <span style="color: #00D4FF; font-weight: bold;">{row['change']}%</span>
                    </div>
                    <div style="margin-bottom: 10px;">
                        {" ".join([f'<span class="signal-badge">{s}</span>' for s in row['signals'].split("; ")])}
                    </div>
                    <div style="display: flex; justify-content: space-between; border-top: 1px solid #333; padding-top: 8px;">
                        <div>
                            <small style="color: #888; display: block;">ENTRY</small>
                            <span class="entry-price">${row['entry']}</span>
                        </div>
                        <div style="text-align: right;">
                            <small style="color: #888; display: block;">STOP LOSS</small>
                            <span class="sl-price">${row['sl_5%']}</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"ANALYZE {row['name']}", key=f"btn_{i}", use_container_width=True):
                st.session_state['selected_stock'] = row['name']
            st.write("")

    # --- ส่วนที่ 2: หน้าจอหลักฝั่งซ้าย (Fixed Graph Area) ---
    selected = st.session_state.get('selected_stock', df['name'].iloc[0])
    stock_info = df[df['name'] == selected].iloc[0]

    # Header & Metrics
    st.markdown(f"## 🛠 {selected} | <span style='color:#00D4FF'>Target 10% Strategy</span>", unsafe_allow_html=True)
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("TP1 (10%)", f"${stock_info['tp1_10%']}")
    m2.metric("TP2 (20%)", f"${stock_info['tp2_20%']}")
    m3.metric("TP3 (30%)", f"${stock_info['tp3_30%']}")
    m4.metric("ENTRY", f"${stock_info['entry']}")

    # กราฟ TradingView (แสดงผล 100% ไม่หาย)
    tv_url = f"https://s.tradingview.com/widgetembed/?symbol={selected}&interval=D&theme=dark"
    st.components.v1.html(
        f'<iframe src="{tv_url}" width="100%" height="650" frameborder="0" style="border: 1px solid #1f2937; border-radius: 8px;"></iframe>', 
        height=660
    )
