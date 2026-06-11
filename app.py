import streamlit as st
import pandas as pd
import os
from datetime import datetime
from twilio.rest import Client

client = Client(
    st.secrets["TWILIO_API_KEY_SID"],
    st.secrets["TWILIO_API_KEY_SECRET"],
    st.secrets["TWILIO_ACCOUNT_SID"]
)
service_sid = st.secrets["TWILIO_MESSAGING_SERVICE_SID"]
PASSWORD = st.secrets["PASSWORD"]

# Auth
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("📢 Advantage Investigations Alert")
    pw = st.text_input("Enter password:", type="password")
    if st.button("Login"):
        if pw == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")
    st.stop()

tab1, tab2 = st.tabs(["🚀 Send Alert", "📜 View Past Broadcasts"])

with tab1:
    st.title("Send Company-Wide Alert")
    st.caption("IT & HR SMS Broadcast Tool • Powered by Twilio")

    csv_files = [f for f in os.listdir(".") if f.endswith(".csv")]
    csv_files.sort()
    selected_csv = st.selectbox("Select file:", csv_files)

    try:
        df = pd.read_csv(selected_csv)
        st.write("**Columns in file:**", list(df.columns))
        
        df.columns = df.columns.str.strip()
        
        # Force phone column
        phone_col = None
        for col in df.columns:
            if 'phone' in col.lower():
                phone_col = col
                break
                
        if not phone_col:
            st.error("No phone column found")
            st.stop()

        st.write(f"Using phone column: **{phone_col}**")

        # Simple cleaning
        def fix_phone(p):
            p = str(p).strip()
            digits = ''.join(filter(str.isdigit, p))
            if len(digits) == 11 and digits.startswith('1'):
                digits = digits[1:]
            if len(digits) == 10:
                return "+1" + digits
            return None

        df["phone"] = df[phone_col].apply(fix_phone)
        df = df.dropna(subset=["phone"]).reset_index(drop=True)
        
        st.success(f"✅ Loaded **{len(df)}** valid recipients")
        
    except Exception as e:
        st.error(f"Error: {e}")
        st.stop()

    username = st.text_input("Your name:", placeholder="Enter your name")
    message = st.text_area("Message:", height=150)

    if st.button("🚀 SEND", type="primary"):
        if not username.strip() or not message.strip():
            st.error("Name and message required")
        else:
            st.info(f"Sending to {len(df)} numbers...")

with tab2:
    st.title("Past Broadcasts")
    if os.path.exists("broadcast_log.csv"):
        st.dataframe(pd.read_csv("broadcast_log.csv"))
