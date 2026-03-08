import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- 1. Page Config & Professional Neon CSS ---
st.set_page_config(page_title="Br8gh1 System", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    /* ล็อคพื้นหลังและสีตัวอักษร */
    .stApp { background-color: #0E1117; color: #E0E0E0; }

    /* ฝั่งซ้ายและกลาง: กราฟ (Fixed) */
    [data-testid="stColumn"]:nth-child(1) {
        position: fixed;
        left: 2rem;
        top: 4rem;
        width: 63%; /* ประมาณ 2 ใน 3 ของหน้าจอ */
        z-index: 100;
    }

    /* ฝั่งขวา: รายชื่อหุ้น (Scrollable) */
    [data-testid="stColumn"]:nth-child(2) {
        margin-left: 66%; /* เว้นที่ให้ฝั่งซ้ายที่โดน Fixed ไว้ */
        height: 90vh;
        overflow-y: auto !important;
        padding-right: 10px;
    }

    /* ตกแต่ง Card หุ้น */
    .stock-card {
        background-color: #161B22;
        border-right: 3px solid #00D4FF;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 8px;
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

# --- 2. Data Loading ---
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

# --- 3. Main Execution ---
try:
    df = load_data()
    if df.empty:
        st.info("⚡ Waiting for scanner data...")
    else:
        # แบ่งสัดส่วน 2:1 (กราฟ 2 ส่วน : หุ้น 1 ส่วน)
        col_graph, col_list = st.columns([2, 1])

        # --- ส่วนที่ 1 & 2: กราฟ (ฝั่งซ้าย-กลาง นิ่งสนิท) ---
        with col_graph:
            selected = st.session_state.get('selected_stock', df['name'].iloc[0])
            stock_info = df[df['name'] == selected].iloc[0]

            # Header & Metrics
            st.markdown(f"## 🛠 {selected} <span style='font-size:1.2rem; color:#00D4FF;'>| Target 10%</span>", unsafe_allow_html=True)
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("TP1 (10%)", f"${stock_info['tp1_10%']}")
            m2.metric("TP2 (20%)", f"${stock_info['tp2_20%']}")
            m3.metric("TP3 (30%)", f"${stock_info['tp3_30%']}")
            m4.metric("STOP (5%)", f"${stock_info['sl_5%']}", delta="-5%", delta_color="inverse")

            # TradingView Chart
            tv_url = f"https://s.tradingview.com/widgetembed/?symbol={selected}&interval=D&theme=dark"
            st.components.v1.html(
                f'<iframe src="{tv_url}" width="100%" height="600" frameborder="0" style="border: 1px solid #1f2937; border-radius: 8px;"></iframe>', 
                height=610
            )

        # --- ส่วนที่ 3: รายชื่อหุ้น (ฝั่งขวา เลื่อนได้) ---
        with col_list:
            st.markdown("### ⚡ **SCANNER**")
            for i, (_, row) in enumerate(df.iterrows()):
                st.markdown(f"""
                    <div class="stock-card">
                        <div style="display: flex; justify-content: space-between;">
                            <span style="font-weight: bold;">{row['name']}</span>
                            <span style="color: #00D4FF;">{row['change']}%</span>
                        </div>
                        <div style="margin-top: 5px;">
                            {" ".join([f'<span class="signal-badge">{s}</span>' for s in row['signals'].split("; ")])}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button(f"VIEW {row['name']}", key=f"btn_{i}", use_container_width=True):
                    st.session_state['selected_stock'] = row['name']
                    st.rerun()
                st.write("")

except Exception as e:
    st.error(f"Waiting for synchronization... {e}")
