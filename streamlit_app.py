import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2.service_account import Credentials

# --- การตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Alpha Scanner Pro", layout="wide")

# --- ฟังก์ชันโหลดข้อมูล ---
@st.cache_data(ttl=600)
def load_data():
    # ดึงค่าจาก Streamlit Secrets (วิธีที่ปลอดภัยที่สุด)
    info = json.loads(st.secrets["gcp_service_account"]["json_data"])
    creds = Credentials.from_service_account_info(info)
    client = gspread.authorize(creds)
    
    # เชื่อมต่อกับ Sheet
    sh = client.open("Stock_Scan_Result")
    worksheet = sh.worksheet("Data_Scan")
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

# --- ส่วนแสดงผลบนหน้าเว็บ ---
st.title("🚀 Alpha Quant Scanner")
st.subheader("Real-time Market Opportunity")

try:
    # เรียกใช้ฟังก์ชันโหลดข้อมูล
    df = load_data()
    
    # แสดงตัวเลขสรุป
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Stocks Found", len(df))
    col2.metric("Market", "US Market")
    col3.metric("Update Status", "Live")

    # แสดงตารางข้อมูล
    st.write("### 📊 Scan Results & Trading Plan")
    st.dataframe(df, use_container_width=True)

    # ส่วนดูรายตัวและกราฟ
    st.divider()
    if not df.empty:
        selected_stock = st.selectbox("เลือกหุ้นเพื่อดูรายละเอียดและกราฟ:", df['name'].unique())
        if selected_stock:
            data = df[df['name'] == selected_stock].iloc[0]
            c1, c2 = st.columns([1, 2])
            with c1:
                st.success(f"**Entry Point:** {data['entry']}")
                st.warning(f"**TP1 (RR 1:1):** {data['tp1_rr1_1']}")
                st.error(f"**Stop Loss:** {data['sl']}")
                st.write(f"**Signal Type:** `{data['signals']}`")
            with c2:
                # แทรกกราฟ TradingView
                chart_url = f"https://s.tradingview.com/widgetembed/?symbol={selected_stock}&interval=D&theme=dark"
                st.components.v1.iframe(chart_url, height=450)
    else:
        st.info("ไม่พบข้อมูลหุ้นในขณะนี้")

except Exception as e:
    st.error(f"เกิดข้อผิดพลาดในการเชื่อมต่อ: {e}")
    st.info("กรุณาตรวจสอบว่าชื่อ Sheet 'Stock_Scan_Result' และ 'Data_Scan' ถูกต้อง และตั้งค่า Secrets เรียบร้อยแล้ว")
