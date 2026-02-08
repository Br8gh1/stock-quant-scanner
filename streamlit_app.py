import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Br8ght Scanner", page_icon="🚀", layout="wide")

@st.cache_data(ttl=300)
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

def render_cards(df, label):
    if df.empty:
        st.info(f"🚫 ไม่พบหุ้นในระบบ {label}")
        return
    cols = st.columns(3)
    for idx, row in df.reset_index().iterrows():
        with cols[idx % 3]:
            with st.container(border=True):
                st.subheader(f"📈 {row['name']}")
                c1, c2 = st.columns(2)
                c1.metric("ENTRY", row['entry'])
                c2.metric("SL", row['sl'], delta_color="inverse")
                st.write("---")
                t1, t2, t3 = st.columns(3)
                t1.caption(f"TP1\n{row['tp1_rr1_1']}")
                t2.caption(f"TP2\n{row['tp2_swing']}")
                t3.caption(f"TP3\n{row['tp3_run_trend']}")
                if st.button(f"Analyze {row['name']}", key=f"{label}_{row['name']}"):
                    st.session_state['selected_stock'] = row['name']

# --- Main App ---
try:
    df = load_data()
    st.title("🚀 Alpha Quant Scanner")

    df_brk = df[df['signals'].str.contains("BREAKOUT", na=False)]
    df_pb  = df[df['signals'].str.contains("PULLBACK", na=False)]
    df_smc = df[df['signals'].str.contains("SMC", na=False)]
    df_mom = df[df['signals'].str.contains("MOMENTUM", na=False)]

    t1, t2, t3, t4 = st.tabs(["🔥 Breakout", "📉 Pullback", "🏦 SMC", "⚡ Momentum"])
    with t1: render_cards(df_brk, "BRK")
    with t2: render_cards(df_pb, "PB")
    with t3: render_cards(df_smc, "SMC")
    with t4: render_cards(df_mom, "MOM")

    st.divider()
    sel = st.session_state.get('selected_stock', df['name'].iloc[0] if not df.empty else "")
    if sel:
        st.subheader(f"📊 Chart: {sel}")
        chart_url = f"https://s.tradingview.com/widgetembed/?symbol={sel}&interval=D&theme=dark"
        st.components.v1.html(f'<iframe src="{chart_url}" width="100%" height="550" frameborder="0"></iframe>', height=560)

except Exception as e:
    st.error(f"รออัปเดตข้อมูล... ({e})")
