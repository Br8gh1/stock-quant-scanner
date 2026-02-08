import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- การตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Alpha Scanner Pro", layout="wide")

# --- เชื่อมต่อ Google Sheets ---
@st.cache_data(ttl=600)
def load_data():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file("key.json", scopes=scope)
    client = gspread.authorize(creds)
    
    # ตรวจสอบชื่อไฟล์ Google Sheets ให้ตรงกับของคุณ
    sh = client.open("Stock_Scan_Result")
    worksheet = sh.worksheet("Data_Scan")
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

# --- ส่วนแสดงผลบนหน้าเว็บ ---
st.title("🚀 Alpha Quant Scanner")

try:
    df = load_data()
    st.success(f"พบหุ้นทั้งหมด {len(df)} ตัวในตาราง")
    st.dataframe(df, use_container_width=True)

    st.divider()
    selected_stock = st.selectbox("เลือกหุ้นเพื่อดูรายละเอียด:", df['name'].unique())
    if selected_stock:
        data = df[df['name'] == selected_stock].iloc[0]
        st.info(f"**Signal:** {data['signals']} | **Entry:** {data['entry']} | **SL:** {data['sl']}")
        
        chart_url = f"https://s.tradingview.com/widgetembed/?symbol={selected_stock}&interval=D&theme=dark"
        st.components.v1.iframe(chart_url, height=450)

except Exception as e:
    st.error(f"เกิดข้อผิดพลาด: {e}")
