import json
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

@st.cache_data(ttl=600)
def load_data():
    # ดึงค่า JSON จาก Secrets มาแปลงกลับเป็น Dictionary
    info = json.loads(st.secrets["gcp_service_account"]["json_data"])
    creds = Credentials.from_service_account_info(info)
    client = gspread.authorize(creds)
    
    sh = client.open("Stock_Scan_Result")
    worksheet = sh.worksheet("Data_Scan")
    data = worksheet.get_all_records()
    return pd.DataFrame(data)
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
   # แก้ไขส่วน load_data() เป็นแบบนี้ครับ
@st.cache_data(ttl=600)
def load_data():
    # ดึงค่าจาก Streamlit Secrets แทนการอ่านไฟล์ key.json
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict)
    client = gspread.authorize(creds)
    
    sh = client.open("Stock_Scan_Result")
    worksheet = sh.worksheet("Data_Scan")
    data = worksheet.get_all_records()
    return pd.DataFrame(data)
    
except Exception as e:
    st.error(f"เกิดข้อผิดพลาด: {e}")
