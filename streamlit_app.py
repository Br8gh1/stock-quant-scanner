import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2.service_account import Credentials

# --- การตั้งค่าหน้าเว็บ (Dark Mode & Layout) ---
st.set_page_config(
    page_title="Alpha Quant Scanner Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ปรับสไตล์ CSS ให้ Card ดูทันสมัย
st.markdown("""
    <style>
    .stContainer {
        border-radius: 15px;
        background-color: #1E1E1E;
        padding: 20px;
        border: 1px solid #333;
        transition: transform 0.3s;
    }
    .stContainer:hover {
        border: 1px solid #00FFCC;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ฟังก์ชันโหลดข้อมูล ---
@st.cache_data(ttl=600)
def load_data():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    # ดึงค่าจาก Secrets (แบบแยกบรรทัดตามที่เราตั้งกันไว้)
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
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

# --- ส่วนแสดงผลหลัก ---
st.title("🚀 Alpha Quant Scanner")
st.caption(f"Last sync: {pd.Timestamp.now(tz='Asia/Bangkok').strftime('%Y-%m-%d %H:%M:%S')} (Bangkok Time)")

try:
    df = load_data()
    
    if not df.empty:
        # ล้างคอลัมน์และเปลี่ยนชื่อให้สวยงาม
        rename_dict = {'tp1_rr1_1': 'TP1', 'tp2_swing': 'TP2', 'tp3_run_trend': 'TP3'}
        df = df.rename(columns=rename_dict)
        if 'change' in df.columns:
            df = df.drop(columns=['change'])

        # --- ส่วนที่ 1: Dashboard Metrics ---
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Signals", len(df))
        m2.metric("Market Status", "OPEN" if 10 <= pd.Timestamp.now(tz='Asia/Bangkok').hour < 17 else "CLOSED")
        m3.metric("System", "Quant V2")
        m4.metric("Strategy", "Reversion")

        st.divider()

        # --- ส่วนที่ 2: Card UI Representation ---
        st.subheader("🎯 Active Trading Signals")
        
        # วาง Card แถวละ 3 ใบ
        cols = st.columns(3)
        for index, row in df.iterrows():
            with cols[index % 3]:
                with st.container(border=True):
                    # ส่วนหัวของ Card
                    st.markdown(f"### **{row['name']}**")
                    st.markdown(f"**Signal:** `{row.get('signals', 'Hold')}`")
                    
                    # ตัวเลขราคา
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write("🟢 **Entry**")
                        st.title(f"{row['entry']}")
                    with c2:
                        st.write("🔴 **Stop Loss**")
                        st.title(f"{row['sl']}")
                    
                    # เป้ากำไร (TP)
                    st.markdown("---")
                    t1, t2, t3 = st.columns(3)
                    t1.caption(f"🏁 TP1\n**{row.get('TP1', 'N/A')}**")
                    t2.caption(f"🏁 TP2\n**{row.get('TP2', 'N/A')}**")
                    t3.caption(f"🏁 TP3\n**{row.get('TP3', 'N/A')}**")
                    
                    # ปุ่มดูรายละเอียดเพื่ออัปเดตกราฟ
                    if st.button(f"Analyze {row['name']}", key=f"btn_{row['name']}", use_container_width=True):
                        st.session_state['selected_stock'] = row['name']

        # --- ส่วนที่ 3: กราฟ TradingView แบบ Full Screen Width ---
        st.divider()
        # ถ้ายังไม่ได้กดปุ่ม ให้เลือกตัวแรกในลิสต์มาโชว์ก่อน
        current_selection = st.session_state.get('selected_stock', df['name'].iloc[0])
        
        st.subheader(f"🔍 Technical Chart: {current_selection}")
        
        chart_html = f"""
        <div style="height:600px;">
            <iframe src="https://s.tradingview.com/widgetembed/?symbol={current_selection}&interval=D&theme=dark&style=1&timezone=Asia%2FBangkok&withdateranges=1&locale=th" 
            width="100%" height="600" frameborder="0" allowtransparency="true" scrolling="no" allowfullscreen></iframe>
        </div>
        """
        st.components.v1.html(chart_html, height=610)

        # แถมตารางดิบไว้ด้านล่างสุด เผื่ออยากเช็คข้อมูลรวม
        with st.expander("View Raw Data Table"):
            st.dataframe(df, use_container_width=True)

    else:
        st.info("🌙 Waiting for signals... The scanner will update during market hours.")

except Exception as e:
    st.error(f"❌ Error during data sync: {e}")
    st.info("Check your Google Sheets structure or Streamlit Secrets configuration.")
