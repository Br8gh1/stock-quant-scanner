import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- 1. การตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Alpha Scanner Pro", page_icon="🚀", layout="wide")

# CSS ปรับแต่ง Metric และ Button ให้ดูทันสมัย
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; font-weight: bold; }
    .stButton > button { width: 100%; border-radius: 8px; border: 1px solid #444; }
    .stButton > button:hover { border: 1px solid #00FFCC; color: #00FFCC; }
    div[data-testid="stExpander"] { border: none !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ฟังก์ชันโหลดข้อมูล ---
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

# --- 3. ส่วนประมวลผลและ UI ---
try:
    df = load_data()
    
    # แก้ไขชื่อคอลัมน์ตาม Logic ใหม่ของคุณ
    rename_dict = {
        'tp1_rr1_1': 'TP1', 
        'tp2_swing': 'TP2', 
        'tp3_run_trend': 'TP3'
    }
    df = df.rename(columns=rename_dict)
    
    # ลบคอลัมน์ที่ไม่จำเป็น
    if 'change' in df.columns:
        df = df.drop(columns=['change'])

    st.title("🚀 Alpha Quant Scanner")
    st.caption("Real-time signals from Quant Model V2")

    if not df.empty:
        # --- แยก Tab ตาม Signal ---
        # กรองเอาเฉพาะสถานะที่มีอยู่จริงใน Sheet มาสร้าง Tab
        unique_signals = sorted(df['signals'].unique().tolist())
        tabs = st.tabs([f"📢 {s.upper()}" for s in unique_signals])

        for i, sig in enumerate(unique_signals):
            with tabs[i]:
                sig_df = df[df['signals'] == sig]
                
                # แสดงผลแบบ Grid (3 คอลัมน์บนจอคอม / ยุบเหลือ 1 บนมือถือ)
                card_cols = st.columns(3)
                for idx, row in sig_df.reset_index().iterrows():
                    with card_cols[idx % 3]:
                        with st.container(border=True):
                            # Header: ชื่อหุ้น
                            st.markdown(f"### **{row['name']}**")
                            
                            # Row 1: Entry & Stop Loss (ใช้ Metric เพื่อความสวยงาม)
                            c1, c2 = st.columns(2)
                            c1.metric("ENTRY", row['entry'])
                            c2.metric("STOP LOSS", row['sl'], delta_color="inverse")
                            
                            st.markdown("---")
                            
                            # Row 2: Take Profit Levels (TP1, TP2, TP3)
                            t1, t2, t3 = st.columns(3)
                            t1.caption(f"🎯 TP1\n**{row.get('TP1', '-')}**")
                            t2.caption(f"🎯 TP2\n**{row.get('TP2', '-')}**")
                            t3.caption(f"🎯 TP3\n**{row.get('TP3', '-')}**")
                            
                            # ปุ่มดูรายละเอียด/กราฟ
                            if st.button(f"Analyze {row['name']}", key=f"btn_{sig}_{row['name']}"):
                                st.session_state['selected_stock'] = row['name']

        # --- ส่วนแสดงกราฟ TradingView ---
        st.divider()
        # เลือกหุ้นตัวแรกของกลุ่มแรกเป็นค่าเริ่มต้นหากยังไม่ได้กดปุ่มใดๆ
        default_stock = df['name'].iloc[0] if not df.empty else ""
        current_stock = st.session_state.get('selected_stock', default_stock)
        
        if current_stock:
            st.subheader(f"📊 Technical Analysis: {current_stock}")
            chart_html = f"""
            <div style="height:550px;">
                <iframe src="https://s.tradingview.com/widgetembed/?symbol={current_stock}&interval=D&theme=dark&style=1&timezone=Asia%2FBangkok&locale=th" 
                width="100%" height="550" frameborder="0" allowtransparency="true" scrolling="no" allowfullscreen></iframe>
            </div>
            """
            st.components.v1.html(chart_html, height=560)
    else:
        st.info("ไม่พบข้อมูลสัญญาณเทรดในขณะนี้")

except Exception as e:
    st.error(f"เกิดข้อผิดพลาด: {e}")
    st.info("คำแนะนำ: ตรวจสอบว่าชื่อคอลัมน์ใน Google Sheets ตรงกับที่ระบุใน rename_dict หรือไม่")
