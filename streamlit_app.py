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
    
    # 2. ดึงค่าจาก Secrets
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
    df = load_data()
    
    if not df.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Stocks", len(df))
        col2.metric("Market", "Global")
        col3.metric("Status", "Online")

        st.write("### 📊 Scan Results")
        st.dataframe(df, use_container_width=True)

        st.divider()
        stock_list = df['name'].unique()
        selected_stock = st.selectbox("เลือกหุ้นเพื่อดูกราฟ:", stock_list)
        
        if selected_stock:
            chart_url = f"https://s.tradingview.com/widgetembed/?symbol={selected_stock}&interval=D&theme=dark"
            st.components.v1.iframe(chart_url, height=450)
    else:
        st.info("ยังไม่มีข้อมูลหุ้นในตาราง")

except Exception as e:
    st.error(f"เกิดข้อผิดพลาดในการเชื่อมต่อ: {e}")
