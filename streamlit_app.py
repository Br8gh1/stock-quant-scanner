import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- 1. Page Config & Strict Layout CSS ---
st.set_page_config(page_title="Alpha Neon Fixed", page_icon="⚡", layout="wide")

# CSS เพื่อบังคับให้หน้าจอไม่เลื่อนทั้งหน้า แต่ให้เลื่อนเฉพาะ Column
st.markdown("""
    <style>
    /* บังคับไม่ให้ Body หลักเลื่อน */
    html, body , [data-testid="stAppViewContainer"] {
        overflow: hidden;
    }

    /* ส่วนของรายการหุ้น (ซ้าย) ให้เลื่อนได้อิสระ */
    [data-testid="stHorizontalBlock"] > div:nth-child(1) {
        height: 100vh;
        overflow-y: auto !important;
        padding-bottom: 100px;
        background-color: #0E1117;
    }

    /* ส่วนของกราฟ (ขวา) ให้ Fixed นิ่งสนิท */
    [data-testid="stHorizontalBlock"] > div:nth-child(2) {
        height: 100vh;
        overflow: hidden !important;
        background-color: #0E1117;
        border-left: 1px solid #1f2937;
    }

    /* ตกแต่ง Card ให้เป็น Neon Style */
    .compact-card {
        background-color: #161B22;
        border-left: 4px solid #00D4FF;
        border-radius: 4px;
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

# --- 2. Data Loading (เหมือนเดิม) ---
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

# --- 3. Compact Card Logic ---
def render_compact_card(row, idx):
    st.markdown(f"""
        <div class="compact-card">
            <div style="display: flex; justify-content: space-between;">
                <span style="font-weight: bold; font-size: 1rem;">{row['name']}</span>
                <span style="color: #00D4FF;">{row['change']}%</span>
            </div>
            <div style="margin: 3px 0;">
                {" ".join([f'<span class="signal-badge">{s}</span>' for s in row['signals'].split("; ")])}
            </div>
        </div>
    """, unsafe_allow_html=True)
    if st.button("VIEW CHART", key=f"btn_{idx}", use_container_width=True):
        st.session_state['selected_stock'] = row['name']
    st.write("")

# --- 4. Main Layout (แบ่ง 2 ฝั่งเด็ดขาด) ---
try:
    df = load_data()
    if df.empty:
        st.error("No data found.")
    else:
        # แบ่งคอลัมน์ [1, 3]
        col_list, col_chart = st.columns([1, 3])

        # --- ฝั่งซ้าย: รายการหุ้น (Scrollable) ---
        with col_list:
            st.markdown("### ⚡ **LIST**")
            # กรองแบ่งกลุ่ม
            df_m = df[df['signals'].str.contains("TREND", na=False)]
            df_p = df[df['signals'].str.contains("PULLBACK", na=False)]
            
            with st.expander("🔥 TREND (MOM)", expanded=True):
                for i, (_, row) in enumerate(df_m.iterrows()):
                    render_compact_card(row, f"m_{i}")
            
            with st.expander("📉 PULLBACK", expanded=True):
                for i, (_, row) in enumerate(df_p.iterrows()):
                    render_compact_card(row, f"p_{i}")

        # --- ฝั่งขวา: กราฟ (Fixed/No Scroll) ---
        with col_chart:
            selected = st.session_state.get('selected_stock', df['name'].iloc[0])
            stock_info = df[df['name'] == selected].iloc[0]

            # Header & Target Metrics (Fixed top of chart)
            st.markdown(f"### 🎯 {selected} | <span style='color:#00D4FF'>Target 10% Strategy</span>", unsafe_allow_html=True)
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("TP1 (10%)", f"${stock_info['tp1_10%']}")
            m2.metric("TP2 (20%)", f"${stock_info['tp2_20%']}")
            m3.metric("TP3 (30%)", f"${stock_info['tp3_30%']}")
            m4.metric("STOP (5%)", f"${stock_info['sl_5%']}", delta="-5%", delta_color="inverse")

            # กราฟ TradingView
            tv_url = f"https://s.tradingview.com/widgetembed/?symbol={selected}&interval=D&theme=dark"
            st.components.v1.html(
                f'<iframe src="{tv_url}" width="100%" height="700" frameborder="0" style="border-radius:10px;"></iframe>', 
                height=720
            )

except Exception as e:
    st.info("System is ready. Awaiting data...")
