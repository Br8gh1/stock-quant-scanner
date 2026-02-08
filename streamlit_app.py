{\rtf1\ansi\ansicpg1252\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import streamlit as st\
import pandas as pd\
import gspread\
from google.oauth2.service_account import Credentials\
\
# --- \uc0\u3585 \u3634 \u3619 \u3605 \u3633 \u3657 \u3591 \u3588 \u3656 \u3634 \u3627 \u3609 \u3657 \u3634 \u3648 \u3623 \u3655 \u3610  ---\
st.set_page_config(page_title="Alpha Scanner Pro", layout="wide")\
\
# --- \uc0\u3648 \u3594 \u3639 \u3656 \u3629 \u3617 \u3605 \u3656 \u3629  Google Sheets ---\
@st.cache_data(ttl=600)\
def load_data():\
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]\
    # \uc0\u3604 \u3638 \u3591 \u3652 \u3615 \u3621 \u3660  key.json \u3607 \u3637 \u3656 \u3588 \u3640 \u3603 \u3629 \u3633 \u3611 \u3650 \u3627 \u3621 \u3604 \u3586 \u3638 \u3657 \u3609  GitHub \u3617 \u3634 \u3651 \u3594 \u3657 \u3591 \u3634 \u3609 \
    creds = Credentials.from_service_account_file("key.json", scopes=scope)\
    client = gspread.authorize(creds)\
    \
    # *** \uc0\u3605 \u3619 \u3623 \u3592 \u3626 \u3629 \u3610 \u3594 \u3639 \u3656 \u3629 \u3652 \u3615 \u3621 \u3660  Google Sheets \u3651 \u3627 \u3657 \u3605 \u3619 \u3591 \u3585 \u3633 \u3610 \u3586 \u3629 \u3591 \u3588 \u3640 \u3603  ***\
    sh = client.open("Stock_Scan_Result")\
    worksheet = sh.worksheet("Data_Scan")\
    data = worksheet.get_all_records()\
    return pd.DataFrame(data)\
\
# --- \uc0\u3626 \u3656 \u3623 \u3609 \u3649 \u3626 \u3604 \u3591 \u3612 \u3621 \u3610 \u3609 \u3627 \u3609 \u3657 \u3634 \u3648 \u3623 \u3655 \u3610  ---\
st.title("\uc0\u55357 \u56960  Alpha Quant Scanner")\
\
try:\
    df = load_data()\
    \
    # \uc0\u3649 \u3626 \u3604 \u3591 \u3605 \u3633 \u3623 \u3648 \u3621 \u3586 \u3626 \u3619 \u3640 \u3611  (Metrics)\
    col1, col2, col3 = st.columns(3)\
    col1.metric("Total Stocks", len(df))\
    col2.metric("Market", "NASDAQ/NYSE/AMEX")\
    col3.metric("Status", "Live Data")\
\
    # \uc0\u3649 \u3626 \u3604 \u3591 \u3605 \u3634 \u3619 \u3634 \u3591 \u3586 \u3657 \u3629 \u3617 \u3641 \u3621 \
    st.write("### \uc0\u55357 \u56522  Scan Results & Trading Plan")\
    st.dataframe(df, use_container_width=True)\
\
    # \uc0\u3626 \u3656 \u3623 \u3609 \u3604 \u3641 \u3619 \u3634 \u3618 \u3605 \u3633 \u3623 \u3649 \u3621 \u3632 \u3585 \u3619 \u3634 \u3615 \
    st.divider()\
    selected_stock = st.selectbox("\uc0\u3648 \u3621 \u3639 \u3629 \u3585 \u3627 \u3640 \u3657 \u3609 \u3648 \u3614 \u3639 \u3656 \u3629 \u3604 \u3641 \u3649 \u3612 \u3609 \u3585 \u3634 \u3619 \u3648 \u3607 \u3619 \u3604 \u3649 \u3621 \u3632 \u3585 \u3619 \u3634 \u3615 :", df['name'].unique())\
    if selected_stock:\
        data = df[df['name'] == selected_stock].iloc[0]\
        c1, c2 = st.columns([1, 2])\
        with c1:\
            st.info(f"**Entry:** \{data['entry']\}")\
            st.warning(f"**TP1:** \{data['tp1_rr1_1']\}")\
            st.error(f"**Stop Loss:** \{data['sl']\}")\
        with c2:\
            chart_url = f"https://s.tradingview.com/widgetembed/?symbol=\{selected_stock\}&interval=D&theme=dark"\
            st.components.v1.iframe(chart_url, height=400)\
\
except Exception as e:\
    st.error(f"\uc0\u3652 \u3617 \u3656 \u3626 \u3634 \u3617 \u3634 \u3619 \u3606 \u3604 \u3638 \u3591 \u3586 \u3657 \u3629 \u3617 \u3641 \u3621 \u3652 \u3604 \u3657 : \{e\}")}