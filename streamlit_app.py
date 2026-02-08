import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials


st.set_page_config(page_title="Br8gh1 System", page_icon="🚀", layout="wide")

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

try:
    df = load_data()
    
    rename_dict = {
        'tp1_rr1_1': 'TP1', 
        'tp2_swing': 'TP2', 
        'tp3_run_trend': 'TP3'
    }
    df = df.rename(columns=rename_dict)

    st.title("🚀 Br8gh1 Logic Scanner v1.1")
    
    if not df.empty:
        
        logic_column = 'strategy' 
        available_logics = sorted(df[logic_column].unique().tolist())
        

        st.info(f"ระบบตรวจพบทั้งหมด **{len(available_logics)} Logic สแกน** ในขณะนี้")
        
        tabs = st.tabs([f"🧪 {logic.upper()}" for logic in available_logics])

        for i, logic_name in enumerate(available_logics):
            with tabs[i]:
            
                logic_df = df[df[logic_column] == logic_name]
                
           
                card_cols = st.columns(3)
                for idx, row in logic_df.reset_index().iterrows():
                    with card_cols[idx % 2]:
                        with st.container(border=True):
                            st.markdown(f"### **{row['name']}**")
                            
                            c1, c2 = st.columns(2)
                            c1.metric("ENTRY", row['entry'])
                            c2.metric("STOP", row['sl'], delta_color="inverse")
                            
                            st.markdown("---")
                            t1, t2, t3 = st.columns(3)
                            t1.caption(f"TP1\n**{row.get('TP1', '-')}**")
                            t2.caption(f"TP2\n**{row.get('TP2', '-')}**")
                            t3.caption(f"TP3\n**{row.get('TP3', '-')}**")
                            
                            if st.button(f"Analyze {row['name']}", key=f"btn_{logic_name}_{row['name']}"):
                                st.session_state['selected_stock'] = row['name']


        st.divider()
        current_stock = st.session_state.get('selected_stock', df['name'].iloc[0] if not df.empty else "")
        if current_stock:
            st.subheader(f"📊 Chart: {current_stock}")
            chart_html = f"""
            <div style="height:500px;">
                <iframe src="https://s.tradingview.com/widgetembed/?symbol={current_stock}&interval=D&theme=dark&style=1&timezone=Asia%2FBangkok&locale=th" 
                width="100%" height="500" frameborder="0" allowtransparency="true" scrolling="no" allowfullscreen></iframe>
            </div>
            """
            st.components.v1.html(chart_html, height=520)

    else:
        st.warning("ไม่มีข้อมูลการสแกน")

except Exception as e:
    st.error(f"Error: {e}")
