import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- 1. การตั้งค่าหน้าจอ ---
st.set_page_config(page_title="Alpha Swing Pro: 10% Target", page_icon="📈", layout="wide")

# --- 2. การเชื่อมต่อ Google Sheets ---
@st.cache_data(ttl=300)
def load_data():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    # ดึงค่าจาก st.secrets (ต้องตั้งค่าใน Streamlit Cloud)
    creds_info = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    client = gspread.authorize(creds)
    
    sh = client.open("Stock_Scan_Result")
    worksheet = sh.worksheet("Data_Scan")
    df = pd.DataFrame(worksheet.get_all_records())
    return df

# --- 3. ฟังก์ชันการแสดงผล Card หุ้น ---
def render_stock_card(row, idx):
    with st.container(border=True):
        # Header: ชื่อหุ้น และการเปลี่ยนแปลงประจำวัน
        col_header1, col_header2 = st.columns([2, 1])
        with col_header1:
            st.markdown(f"### **{row['name']}**")
        with col_header2:
            change = row['change']
            st.markdown(f"**{'+' if change > 0 else ''}{change}%**", 
                        help="Daily Price Change")

        # Signals Badge
        signals = row['signals'].split("; ")
        badge_html = "".join([f'<span style="background-color: #1E3A8A; color: white; padding: 2px 8px; border-radius: 10px; margin-right: 5px; font-size: 0.7rem;">{s}</span>' for s in signals])
        st.markdown(badge_html, unsafe_allow_html=True)
        st.write("")

        # แถว Entry & SL
        c1, c2 = st.columns(2)
        c1.metric("ENTRY", f"${row['entry']}")
        # คำนวณ % Loss จาก SL จริง
        sl_val = row['sl_5%']
        c2.metric("STOP LOSS", f"${sl_val}", delta="-5.0%", delta_color="inverse")

        st.divider()

        # ส่วนของ Take Profit (TP)
        st.caption("🎯 TAKE PROFIT TARGETS")
        tp_cols = st.columns(3)
        
        # TP1 (10% - Primary Target)
        with tp_cols[0]:
            st.markdown(f"<div style='text-align: center; background-color: #065F46; padding: 5px; border-radius: 5px;'>"
                        f"<small style='color: #A7F3D0;'>TP1 (10%)</small><br>"
                        f"<b>${row['tp1_10%']}</b></div>", unsafe_allow_html=True)
        
        # TP2 (20% - Swing)
        with tp_cols[1]:
            st.markdown(f"<div style='text-align: center; background-color: #064E3B; padding: 5px; border-radius: 5px;'>"
                        f"<small style='color: #A7F3D0;'>TP2 (20%)</small><br>"
                        f"<b>${row['tp2_20%']}</b></div>", unsafe_allow_html=True)
            
        # TP3 (30% - Trend)
        with tp_cols[2]:
            st.markdown(f"<div style='text-align: center; background-color: #022C22; padding: 5px; border-radius: 5px;'>"
                        f"<small style='color: #A7F3D0;'>TP3 (30%)</small><br>"
                        f"<b>${row['tp3_30%']}</b></div>", unsafe_allow_html=True)

        st.write("")
        if st.button(f"View Chart: {row['name']}", key=f"btn_{idx}", use_container_width=True):
            st.session_state['selected_stock'] = row['name']

# --- 4. Main UI ---
st.title("🚀 Alpha Swing Pro: 10% Target Strategy")
st.info("Strategy: Swing Trading in Large Caps | TP1: 10% | SL: 5% (RR 1:2)")

try:
    df_raw = load_data()
    
    if df_raw.empty:
        st.warning("No stocks matched the signal today. Scanning for 'Trend Starter' or 'Quality Pullback'...")
    else:
        # แยก Tab ตามสัญญาณ
        tab1, tab2 = st.tabs(["🔥 Trend Starters", "📉 Quality Pullbacks"])

        with tab1:
            df_trend = df_raw[df_raw['signals'].str.contains("TREND", na=False)]
            if not df_trend.empty:
                cols = st.columns(3)
                for i, (_, row) in enumerate(df_trend.iterrows()):
                    with cols[i % 3]:
                        render_stock_card(row, f"trend_{i}")
            else:
                st.write("No Trend Starter setups found.")

        with tab2:
            df_pb = df_raw[df_raw['signals'].str.contains("PULLBACK", na=False)]
            if not df_pb.empty:
                cols = st.columns(3)
                for i, (_, row) in enumerate(df_pb.iterrows()):
                    with cols[i % 3]:
                        render_stock_card(row, f"pb_{i}")
            else:
                st.write("No Pullback setups found.")

    # --- 5. TradingView Widget Section ---
    st.divider()
    selected_symbol = st.session_state.get('selected_stock', df_raw['name'].iloc[0] if not df_raw.empty else None)
    
    if selected_symbol:
        st.subheader(f"📊 Live Analysis: {selected_symbol}")
        # ใส่ Widget TradingView
        tv_url = f"https://s.tradingview.com/widgetembed/?symbol={selected_symbol}&interval=D&theme=dark"
        st.components.v1.html(f'<iframe src="{tv_url}" width="100%" height="600" frameborder="0"></iframe>', height=610)

except Exception as e:
    st.error(f"Error loading dashboard: {e}")
    st.info("Please make sure the Google Colab scanner has finished running and updated the sheet.")

# --- Footer ---
st.caption("Alpha Swing Pro © 2024 | Data refreshed every 5 minutes.")
