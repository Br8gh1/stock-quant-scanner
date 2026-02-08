import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- การตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Alpha Scanner Pro", layout="wide")

# --- ฟังก์ชันโหลดข้อมูล ---
@st.cache_data(ttl=600)
def load_data():
    # 1. กำหนดขอบเขตการเข้าถึง (Scope)
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    # 2. ดึงค่าจาก Secrets (ต้องตั้งค่าใน Streamlit Cloud Secrets ก่อน)
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
    
    # 3. สร้าง Credentials พร้อม Scope
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    client = gspread.authorize(creds)
    
    # 4. เชื่อมต่อกับ Sheet
    sh = client.open("Stock_Scan_Result")
    worksheet = sh.worksheet("Data_Scan")
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

# --- ส่วนแสดงผลบนหน้าเว็บ ---
st.title("🚀 Alpha Quant Scanner")
st.subheader("Real-time Market Opportunity")

try:
    # โหลดข้อมูล
    df = load_data()
    
    if not df.empty:
        # --- 1. จัดการชื่อหัวตารางและคอลัมน์ ---
        # เปลี่ยนชื่อคอลัมน์ (ตรวจสอบให้แน่ใจว่าชื่อเดิมใน Google Sheet สะกดถูกต้องตามนี้)
        rename_dict = {
            'tp1_rr1_1': 'TP1',
            'tp2_swing': 'TP2',
            'tp3_run_trend': 'TP3'
        }
        df = df.rename(columns=rename_dict)

        # ตัดคอลัมน์ 'change' ออก (ถ้ามี)
        if 'change' in df.columns:
            df = df.drop(columns=['change'])

        # --- 2. แสดงตัวเลขสรุป ---
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Stocks", len(df))
        col2.metric("Market Status", "Data Loaded")
        col3.metric("Scan Type", "Quant Model V1")

        # --- 3. แสดงตารางข้อมูล ---
        st.write("### 📊 Trading Plan Table")
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.divider()
        
        # --- 4. ส่วนแสดงกราฟ TradingView ---
        st.subheader("🔍 Technical Chart Analysis")
        
        stock_list = df['name'].unique().tolist()
        selected_stock = st.selectbox("เลือกชื่อหุ้นเพื่อดูรายละเอียดและกราฟ:", stock_list)
        
        if selected_stock:
            # ดึงข้อมูลตัวที่เลือกมาโชว์เหนือรูปกราฟ
            sd = df[df['name'] == selected_stock].iloc[0]
            
            m1, m2, m3, m4 = st.columns(4)
            m1.success(f"**Entry:** {sd.get('entry', 'N/A')}")
            m2.info(f"**TP1:** {sd.get('TP1', 'N/A')}")
            m3.info(f"**TP2:** {sd.get('TP2', 'N/A')}")
            m4.error(f"**SL:** {sd.get('sl', 'N/A')}")

            # Embed TradingView
            chart_html = f"""
            <div style="height:550px;">
                <iframe src="https://s.tradingview.com/widgetembed/?symbol={selected_stock}&interval=D&theme=dark&style=1&timezone=Asia%2FBangkok&withdateranges=1&locale=th" 
                width="100%" height="550" frameborder="0" allowtransparency="true" scrolling="no" allowfullscreen></iframe>
            </div>
            """
            st.components.v1.html(chart_html, height=560)
            
    else:
        st.info("ยังไม่มีข้อมูลหุ้นในตาราง")

except Exception as e:
    st.error(f"เกิดข้อผิดพลาดในการแสดงผล: {e}")
    st.info("คำแนะนำ: ตรวจสอบชื่อหัวคอลัมน์ใน Google Sheets ว่าตรงกับที่โค้ดเรียกใช้หรือไม่")
