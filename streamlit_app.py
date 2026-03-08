import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- 1. Page Config ---
st.set_page_config(page_title="Br8gh1 System", page_icon="⚡", layout="wide")

# --- 2. Improved Strict CSS ---
st.markdown("""
    <style>
    /* บังคับพื้นหลัง */
    .stApp { background-color: #0E1117; }

    /* ส่วนรายการหุ้น (ฝั่งซ้าย) */
    [data-testid="stColumn"]:nth-child(1) {
        height: 100vh;
        overflow-y: auto !important;
        padding-right: 20px;
        padding-bottom: 100px;
    }

    /* ส่วนกราฟ (ฝั่งขวา) - บังคับให้ Fixed อยู่กับที่ */
    [data-testid="stColumn"]:nth-child(2) {
        position: fixed;
        right: 0;
        top: 0;
        width: 74%; /* ปรับให้พอดีกับ layout [1, 3] */
        height: 100vh;
        padding: 20px;
        background-color: #0E1117;
        z-index: 99;
        overflow: hidden;
    }

    /* ตกแต่ง Card */
    .compact-card {
        background-color: #161B22;
        border-left: 4px solid #00D4FF;
        border-radius: 4px;
        padding: 12px;
        margin-bottom: 8px;
    }
    .signal-badge {
        color: #00D4FF;
        border: 1px solid #00D4FF;
        padding: 0px 6px;
        border-radius: 3px;
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

# --- 4. Card Component ---
def render_compact_card(row, idx):
    st.markdown(f"""
        <div class="compact-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: bold; font-size: 1.1rem; color: white;">{row['name']}</span>
                <span style="color: #00D4FF; font-weight: bold;">{row['change']}%</span>
            </div>
            <div style="margin: 6px 0;">
                {" ".join([f'<span class="signal-badge">{s}</span>' for s in row['signals'].split("; ")])}
            </div>
            <div style="font-size: 0.85rem; color: #888;">
                In: ${row['entry']} | SL: ${row['sl_5%']}
            </div>
        </div>
    """, unsafe_allow_html=True)
    if st.button("VIEW CHART", key=f"btn_{idx}", use_container_width=True):
        st.session_state['selected_stock'] = row['name']
    st.write("")

# --- 5. Main Layout ---
try:
    df = load_data()
    if df.empty:
        st.error("Waiting for Data...")
    else:
        # ใช้ Column สัดส่วน 1:3
        col_list, col_chart = st.columns([1, 3])

        # --- ฝั่งซ้าย: LIST ---
        with col_list:
            st.markdown("<h2 style='color: white;'>⚡ LIST</h2>", unsafe_allow_html=True)
            for i, (_, row) in enumerate(df.iterrows()):
                render_compact_card(row, f"card_{i}")

        # --- ฝั่งขวา: CHART (Fixed) ---
        with col_chart:
            selected = st.session_state.get('selected_stock', df['name'].iloc[0])
            stock_info = df[df['name'] == selected].iloc[0]

            # Header & Metrics
            st.markdown(f"""
                <div style="margin-bottom: 10px;">
                    <h1 style="color: white; margin-bottom: 0;">{selected} <span style="font-size: 1.2rem; color: #00D4FF;">Target 10% Strategy</span></h1>
                </div>
            """, unsafe_allow_html=True)
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("TP1 (10%)", f"${stock_info['tp1_10%']}")
            m2.metric("TP2 (20%)", f"${stock_info['tp2_20%']}")
            m3.metric("TP3 (30%)", f"${stock_info['tp3_30%']}")
            m4.metric("STOP (5%)", f"${stock_info['sl_5%']}", delta="-5%", delta_color="inverse")

            # Chart Container
            tv_url = f"https://s.tradingview.com/widgetembed/?symbol={selected}&interval=D&theme=dark&style=1&timezone=Etc%2FUTC"
            st.components.v1.html(
                f"""
                <iframe src="{tv_url}" 
                        width="100%" 
                        height="600" 
                        frameborder="0" 
                        style="border: 1px solid #1f2937; border-radius: 8px;">
                </iframe>
                """, 
                height=610
            )

except Exception as e:
    st.info("System initializing...")
