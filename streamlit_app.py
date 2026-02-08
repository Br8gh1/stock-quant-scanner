import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- 1. การตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Alpha Quant Scanner", page_icon="🚀", layout="wide")

# CSS ปรับแต่ง Metric และ UI สำหรับมือถือ
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; }
    .stButton > button { width: 100%; border-radius: 10px; height: 3em; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #1e1e1e; border-radius: 5px 5px 0 0; padding: 10px 20px;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=600)
def load_data():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_info = {
        "type": st.secrets["gcp_service_account"]["type"],
        "project_id": st.secrets["gcp_service_account"]["project_id"],
        "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
        "private_key": st.secrets["gcp_service_account"]["private_key"],
        "client_email": st.secrets["gcp_service_account"]["client_email"],
        "client_id": st.secrets["gcp_service_account"]["client_id"],
        "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
        "token_uri": st.secrets["gcp_service_account"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"],
        "universe_domain": st.secrets["gcp_service_account"]["universe_domain"],
    }
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    client = gspread.authorize(creds)
    sh = client.open("Stock_Scan_Result")
    worksheet = sh.worksheet("Data_Scan")
    return pd.DataFrame(worksheet.get_all_records())

def render_cards(df, strategy_name):
    if df.empty:
        st.info(f"🚫 No result for {strategy_name} strategy.")
        return
    
    # Grid ระบบ 3 คอลัมน์ (จะปรับเป็น 1 อัตโนมัติบนมือถือ)
    cols = st.columns(3)
    for idx, row in df.reset_index().iterrows():
        with cols[idx % 3]:
            with st.container(border=True):
                st.markdown(f"### **{row['name']}**")
                st.caption(f"Strategy: {strategy_name}")
                
                m1, m2 = st.columns(2)
                m1.metric("ENTRY", row['entry'])
                m2.metric("SL", row['sl'], delta_color="inverse")
                
                st.markdown("---")
                t1, t2, t3 = st.columns(3)
                t1.caption(f"TP1\n**{row.get('TP1', '-')}**")
                t2.caption(f"TP2\n**{row.get('TP2', '-')}**")
                t3.caption(f"TP3\n**{row.get('TP3', '-')}**")
                
                if st.button(f"Analyze {row['name']}", key=f"btn_{strategy_name}_{row['name']}"):
                    st.session_state['selected_stock'] = row['name']

# --- 2. ส่วนประมวลผลหลัก ---
try:
    raw_df = load_data()
    # Rename หัวตารางตามที่คุณต้องการ
    df = raw_df.rename(columns={
        'tp1_rr1_1': 'TP1', 
        'tp2_swing': 'TP2', 
        'tp3_run_trend': 'TP3'
    })

    st.title("🚀 Br8gh1 Multi-Strategy Scanner")

    # --- 3. การทำ Logic Filtering ---
    # 1. BREAKOUT
    df_breakout = df[df['close'] >= df['high20']]

    # 2. PULLBACK (ย่อตัวใกล้ MA20 ไม่เกิน 2.5%)
    # Logic: close >= ma20 AND ((close - ma20) / ma20) <= 0.025
    df_pullback = df[
        (df['close'] >= df['ma20']) & 
        ((df['close'] - df['ma20']) / df['ma20'] <= 0.025)
    ]

    # 3. SMC (Equal Lows: หาจุดต่ำสุด 10 วัน และ 20 วัน ที่ใกล้เคียงกันมาก)
    # Logic: abs(low10 - low20) / low20 < 0.005 (ต่างกันไม่เกิน 0.5%)
    df_smc = df[abs(df['low10'] - df['low20']) / df['low20'] < 0.005]

    # 4. MOMENTUM (Price > MA10 > MA20)
    df_momentum = df[
        (df['close'] > df['ma10']) & 
        (df['ma10'] > df['ma20'])
    ]

    # --- 4. การแสดงผลแบบ Tab ---
    tab1, tab2, tab3, tab4 = st.tabs(["🔥 BREAKOUT", "📉 PULLBACK", "🏦 SMC (Equal Lows)", "⚡ MOMENTUM"])

    with tab1: render_cards(df_breakout, "BREAKOUT")
    with tab2: render_cards(df_pullback, "PULLBACK")
    with tab3: render_cards(df_smc, "SMC")
    with tab4: render_cards(df_momentum, "MOMENTUM")

    # --- 5. ส่วนแสดงกราฟ ---
    st.divider()
    current_stock = st.session_state.get('selected_stock', "")
    if current_stock:
        st.subheader(f"📊 Technical Chart: {current_stock}")
        chart_html = f"""
        <div style="height:550px;">
            <iframe src="https://s.tradingview.com/widgetembed/?symbol={current_stock}&interval=D&theme=dark&style=1&timezone=Asia%2FBangkok&locale=th" 
            width="100%" height="550" frameborder="0" allowtransparency="true" scrolling="no" allowfullscreen></iframe>
        </div>
        """
        st.components.v1.html(chart_html, height=560)
    else:
        st.info("💡 Select a stock from any strategy tab to view the chart.")

except Exception as e:
    st.error(f"Error: {e}")
    st.info("กรุณาตรวจสอบว่า Google Sheets มีคอลัมน์: close, high20, low10, low20, ma10, ma20")
