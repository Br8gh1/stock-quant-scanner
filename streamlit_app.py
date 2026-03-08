import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- 1. Page Config & Neon Style ---
st.set_page_config(page_title="Br8gh1 System Pro", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    
    /* ตกแต่ง Card หุ้นด้านล่าง */
    .stock-card {
        background-color: #161B22;
        border: 1px solid #1f2937;
        border-top: 3px solid #00D4FF;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        transition: 0.3s;
    }
    .stock-card:hover {
        border-color: #00D4FF;
        box-shadow: 0 0 10px rgba(0, 212, 255, 0.2);
    }
    .signal-tag {
        background-color: #003366;
        color: #00D4FF;
        padding: 2px 8px;
        border-radius: 5px;
        font-size: 0.7rem;
        font-weight: bold;
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
    except Exception as e:
        st.error(f"Error connecting to Sheets: {e}")
        return pd.DataFrame()

# --- 3. Main Execution ---
try:
    df = load_data()
    
    if df.empty:
        st.info("⚡ System is active. Waiting for scanner data from Google Sheets...")
    else:
        # --- SECTION 1: CHART & METRICS (Fixed Top) ---
        # เลือกหุ้นตัวแรกเป็นค่าเริ่มต้น
        selected_symbol = st.session_state.get('selected_stock', df['name'].iloc[0])
        stock_info = df[df['name'] == selected_symbol].iloc[0]

        st.markdown(f"## 🛠 {selected_symbol} | <span style='color:#00D4FF'>Target 10% Strategy</span>", unsafe_allow_html=True)
        
        # แสดงตัวเลข TP/SL
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("TP1 (10%)", f"${stock_info['tp1_10%']}")
        m2.metric("TP2 (20%)", f"${stock_info['tp2_20%']}")
        m3.metric("TP3 (30%)", f"${stock_info['tp3_30%']}")
        m4.metric("STOP (5%)", f"${stock_info['sl_5%']}", delta="-5%", delta_color="inverse")

        # กราฟ TradingView ตัวใหญ่
        tv_url = f"https://s.tradingview.com/widgetembed/?symbol={selected_symbol}&interval=D&theme=dark"
        st.components.v1.html(
            f'<iframe src="{tv_url}" width="100%" height="550" frameborder="0" style="border-radius:10px;"></iframe>', 
            height=560
        )

        st.divider()

        # --- SECTION 2: STOCK LIST (Scrollable Section Below) ---
        st.markdown("### ⚡ **SCANNER RESULTS** (Select a stock to update chart)")
        
        # กรองแบ่งกลุ่มสัญญาณ
        tabs = st.tabs(["🔥 Trend Starters", "📉 Pullback Setups"])
        
        with tabs[0]:
            df_m = df[df['signals'].str.contains("TREND", na=False)]
            if not df_m.empty:
                # แสดงผลเป็น Grid 4 คอลัมน์
                cols = st.columns(4)
                for i, (_, row) in enumerate(df_m.iterrows()):
                    with cols[i % 4]:
                        st.markdown(f"""
                            <div class="stock-card">
                                <div style="font-size: 1.2rem; font-weight: bold;">{row['name']}</div>
                                <div style="color: #00D4FF; font-size: 1rem;">{row['change']}%</div>
                                <div style="margin: 8px 0;">{" ".join([f'<span class="signal-tag">{s}</span>' for s in row['signals'].split("; ")])}</div>
                            </div>
                        """, unsafe_allow_html=True)
                        if st.button("VIEW CHART", key=f"m_{i}", use_container_width=True):
                            st.session_state['selected_stock'] = row['name']
                            st.rerun() # บังคับ Refresh เพื่อเลื่อนกราฟขึ้นไปดูด้านบน
            else:
                st.write("No trend setups found.")

        with tabs[1]:
            df_p = df[df['signals'].str.contains("PULLBACK", na=False)]
            if not df_p.empty:
                cols = st.columns(4)
                for i, (_, row) in enumerate(df_p.iterrows()):
                    with cols[i % 4]:
                        st.markdown(f"""
                            <div class="stock-card">
                                <div style="font-size: 1.2rem; font-weight: bold;">{row['name']}</div>
                                <div style="color: #00D4FF; font-size: 1rem;">{row['change']}%</div>
                                <div style="margin: 8px 0;">{" ".join([f'<span class="signal-tag">{s}</span>' for s in row['signals'].split("; ")])}</div>
                            </div>
                        """, unsafe_allow_html=True)
                        if st.button("VIEW CHART", key=f"p_{i}", use_container_width=True):
                            st.session_state['selected_stock'] = row['name']
                            st.rerun()
            else:
                st.write("No pullback setups found.")

except Exception as e:
    st.error(f"Something went wrong: {e}")
