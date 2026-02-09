import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Br8ght Scanner", page_icon="🚀", layout="wide")

# ----------------------------
# Google Sheets loader
# ----------------------------
@st.cache_data(ttl=300)
def load_sheets():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    sa = st.secrets["gcp_service_account"]
    creds_info = {
        "type": sa["type"],
        "project_id": sa["project_id"],
        "private_key_id": sa["private_key_id"],
        "private_key": sa["private_key"],
        "client_email": sa["client_email"],
        "client_id": sa["client_id"],
        "auth_uri": sa["auth_uri"],
        "token_uri": sa["token_uri"],
        "auth_provider_x509_cert_url": sa["auth_provider_x509_cert_url"],
        "client_x509_cert_url": sa["client_x509_cert_url"],
        "universe_domain": sa.get("universe_domain", "googleapis.com"),
    }
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    client = gspread.authorize(creds)

    sh = client.open("Stock_Scan_Result")

    def read_ws(name: str) -> pd.DataFrame:
        ws = sh.worksheet(name)
        df = pd.DataFrame(ws.get_all_records())
        # normalize columns (lowercase + strip)
        df.columns = [str(c).strip().lower() for c in df.columns]
        return df

    df_data = read_ws("Data_Scan")
    df_long = read_ws("LONG_TERM_CORE")
    df_swing = read_ws("SWING_SETUPS")

    # make sure name exists and is string
    for d in (df_data, df_long, df_swing):
        if "name" in d.columns:
            d["name"] = d["name"].astype(str)

    return df_data, df_long, df_swing


# ----------------------------
# UI helpers
# ----------------------------
def safe_get(row, key, default=""):
    k = key.lower()
    return row.get(k, default)

def render_cards(df: pd.DataFrame, label: str, show_action=False):
    if df.empty:
        st.info(f"🚫 ไม่พบหุ้นในระบบ {label}")
        return

    cols = st.columns(3)
    for idx, row in df.reset_index(drop=True).iterrows():
        with cols[idx % 3]:
            with st.container(border=True):
                name = safe_get(row, "name", "")
                st.subheader(f"📈 {name}")

                if show_action:
                    action = safe_get(row, "action", "")
                    reason = safe_get(row, "reason", "")
                    if action:
                        st.caption(f"**Action:** {action}")
                    if reason:
                        st.caption(f"**Reason:** {reason}")

                c1, c2 = st.columns(2)
                c1.metric("ENTRY", safe_get(row, "entry", "-"))
                c2.metric("SL", safe_get(row, "sl", "-"), delta_color="inverse")

                # TP fields may not exist in LONG/SWING sheets (your new scan exports tp2_swing only)
                st.write("---")
                t1, t2, t3 = st.columns(3)
                t1.caption(f"TP1\n{safe_get(row, 'tp1_rr1_1', '-')}")
                t2.caption(f"TP2\n{safe_get(row, 'tp2_swing', '-')}")
                t3.caption(f"TP3\n{safe_get(row, 'tp3_run_trend', '-')}")

                # Optional valuation fields
                vg = safe_get(row, "valuation_gap", None)
                fv = safe_get(row, "fv_base", None)
                if vg not in [None, "", "-"] or fv not in [None, "", "-"]:
                    with st.expander("Valuation", expanded=False):
                        st.write(f"**FV Base:** {fv}")
                        st.write(f"**Valuation Gap (%):** {vg}")

                if st.button(f"Analyze {name}", key=f"{label}_{name}_{idx}"):
                    st.session_state["selected_stock"] = name


def normalize_for_tabs(df: pd.DataFrame) -> pd.DataFrame:
    # Ensure signals column exists
    if "signals" not in df.columns:
        df["signals"] = ""
    df["signals"] = df["signals"].astype(str)
    return df


# ----------------------------
# Main App
# ----------------------------
try:
    df_data, df_long, df_swing = load_sheets()

    st.title("🚀 Alpha Quant Scanner")

    # Sidebar quick stats
    with st.sidebar:
        st.header("📌 Overview")
        st.metric("Data_Scan", len(df_data))
        st.metric("LONG_TERM_CORE", len(df_long))
        st.metric("SWING_SETUPS", len(df_swing))
        st.caption("Auto refresh every 5 minutes")

    # Tabs: original technical tabs + new LONG/SWING tabs
    df_data = normalize_for_tabs(df_data)

    df_brk = df_data[df_data["signals"].str.contains("BREAKOUT", na=False)]
    df_pb  = df_data[df_data["signals"].str.contains("PULLBACK", na=False)]
    df_smc = df_data[df_data["signals"].str.contains("SMC", na=False)]
    df_mom = df_data[df_data["signals"].str.contains("MOMENTUM", na=False)]

    t1, t2, t3, t4, t5, t6 = st.tabs(
        ["🔥 Breakout", "📉 Pullback", "🏦 SMC", "⚡ Momentum", "🧱 LONG_TERM_CORE", "🎯 SWING_SETUPS"]
    )

    with t1:
        render_cards(df_brk, "BRK")
    with t2:
        render_cards(df_pb, "PB")
    with t3:
        render_cards(df_smc, "SMC")
    with t4:
        render_cards(df_mom, "MOM")

    with t5:
        # LONG_TERM_CORE
        render_cards(df_long, "LONG", show_action=True)

    with t6:
        # SWING_SETUPS
        render_cards(df_swing, "SWING", show_action=True)

    st.divider()

    # Chart section: allow selecting from all sources
    all_names = []
    for d in (df_data, df_long, df_swing):
        if "name" in d.columns and not d.empty:
            all_names.extend(d["name"].dropna().astype(str).tolist())

    all_names = sorted(list(dict.fromkeys(all_names)))  # unique preserve order

    default_sel = st.session_state.get("selected_stock", all_names[0] if all_names else "")
    sel = st.selectbox("Select stock", options=all_names, index=all_names.index(default_sel) if default_sel in all_names else 0) if all_names else ""

    if sel:
        st.session_state["selected_stock"] = sel
        st.subheader(f"📊 Chart: {sel}")
        # if your sheet stores just ticker, keep it
        # if it stores full exchange like NASDAQ:TSLA, you can detect it here
        symbol = sel
        chart_url = f"https://s.tradingview.com/widgetembed/?symbol={symbol}&interval=D&theme=dark"
        st.components.v1.html(
            f'<iframe src="{chart_url}" width="100%" height="550" frameborder="0"></iframe>',
            height=560,
        )

except Exception as e:
    st.error(f"รออัปเดตข้อมูล... ({e})")
