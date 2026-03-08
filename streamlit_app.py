import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- 1. Page Config & Fixed Layout CSS ---
st.set_page_config(page_title="Alpha Neon Fixed", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    
    /* สร้าง Scrollbar ให้ฝั่งรายการหุ้น (ซ้าย) */
    [data-testid="stVerticalBlock"] > div:has(div.stColumn) > div.stColumn:first-child {
        height: 90vh;
        overflow-y: auto;
        padding-right: 10px;
    }

    /* ตรึงตำแหน่งฝั่งกราฟ (ขวา) ให้ Fixed */
    [data-testid="stVerticalBlock"] > div:has(div.stColumn) > div.stColumn:last-child {
        position: sticky;
        top: 20px;
        height: 90vh;
    }

    /* Neon Style สำหรับ Card */
    .compact-card {
        background-color: #161B22;
        border: 1px solid #1f2937;
        border-left: 4px solid #00D4FF;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
        transition: 0.3s;
    }
    .compact-card:hover {
        border-color: #00D4FF;
        box-shadow: 0 0 10px rgba(0, 212, 255, 0.3);
    }
    
    .signal-badge {
        background-color: #001a33;
        color: #00D4FF;
        border: 1px solid #00D4FF;
        padding: 1px 6px;
        border-radius: 4px;
        font-size: 0.65rem;
        font-weight: bold;
        margin-right: 3px;
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

# --- 3. Compact Card Logic ---
def render_compact_card(row, idx):
    # ใช้ HTML ร่วมกับ Streamlit Button
    st.markdown(f"""
        <div class="compact-card">
            <div style="display: flex; justify-content: space-between;">
                <span style="font-weight: bold; font-size: 1.1rem;">{row['name']}</span>
                <span style="color: #00D4FF;">{row['change']}%</span>
            </div>
            <div style="margin: 5px 0;">
                {" ".join([f'<span class="signal-badge">{s}</span>' for s in row['signals'].split("; ")])}
            </div>
            <div style="font-size: 0.8rem; color: #888;">
                In: ${row['entry']} | SL: ${row['sl_5%']}
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("👁️ VIEW CHART", key=f"btn_{idx}", use_container_width=True):
        st.session_state['selected_stock'] = row['name']
    st.write("")

# --- 4. Main Layout (Left Scroll | Right Fixed) ---
try:
    df = load_data()
    
    if df.empty:
        st.error("No data found. Please run the scanner first.")
    else:
        # แบ่งคอลัมน์ [1:3]
        col_list, col_chart = st.columns([1, 3])

        with col_list:
            st.markdown("### ⚡ **SCANNER**")
            # กรองแบ่งกลุ่มง่ายๆ
            df_m = df[df['signals'].str.contains("TREND", na=False)]
            df_p = df[df['signals'].str.contains("PULLBACK", na=False)]
            
            with st.expander("🔥 TREND STARTER", expanded=True):
                for i, (_, row) in enumerate(df_m.iterrows()):
                    render_compact_card(row, f"m_{i}")
            
            with st.expander("📉 PULLBACK", expanded=False):
                for i, (_, row) in enumerate(df_p.iterrows()):
                    render_compact_card(row, f"p_{i}")

        with col_chart:
            # เลือกหุ้นตัวแรกถ้ายังไม่ได้เลือก
            selected = st.session_state.get('selected_stock', df['name'].iloc[0])
            stock_info = df[df['name'] == selected].iloc[0]

            # Header ข้อมูลเป้าหมาย
            st.markdown(f"""
                <div style="background: linear-gradient(90deg, #161B22 0%, #0E1117 100%); padding: 15px; border-radius: 10px; border-bottom: 2px solid #00D4FF; margin-bottom: 15px;">
                    <span style="font-size: 2rem; font-weight: bold;">{selected}</span>
                    <span style="margin-left: 20px; color: #888;">Target 10% Strategy</span>
                </div>
            """, unsafe_allow_html=True)

            # Metrics Row
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("TP1 (10%)", f"${stock_info['tp1_10%']}")
            m2.metric("TP2 (20%)", f"${stock_info['tp2_20%']}")
            m3.metric("TP3 (30%)", f"${stock_info['tp3_30%']}")
            m4.metric("STOP (5%)", f"${stock_info['sl_5%']}", delta="-5%", delta_color="inverse")

            # Chart Container (Height 650px)
            tv_url = f"https://s.tradingview.com/widgetembed/?symbol={selected}&interval=D&theme=dark"
            st.components.v1.html(f'<iframe src="{tv_url}" width="100%" height="650" frameborder="0"></iframe>', height=660)

except Exception as e:
    st.info("⚡ System is ready. Please select a stock or check your connection.")
