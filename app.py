import streamlit as st
import pandas as pd
import os
from datetime import datetime
from twilio.rest import Client

# ====================== SECRETS ======================
client = Client(
    st.secrets["TWILIO_API_KEY_SID"],
    st.secrets["TWILIO_API_KEY_SECRET"],
    st.secrets["TWILIO_ACCOUNT_SID"]
)
service_sid = st.secrets["TWILIO_MESSAGING_SERVICE_SID"]
PASSWORD = st.secrets["PASSWORD"]

# ====================== PASSWORD + USERNAME ======================
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

# Username (for logging)
username = st.text_input("Your name (for logging):", value="IT/HR User")

# ====================== CSV SELECTOR ======================
st.title("🚀 Send Company-Wide Alert")
st.caption("IT & HR SMS Broadcast Tool • Powered by Twilio")

# Find all CSV files automatically
csv_files = [f for f in os.listdir(".") if f.endswith(".csv")]
csv_files.sort()

if not csv_files:
    st.error("No .csv files found in the folder.")
    st.stop()

selected_csv = st.selectbox("Select employee list to send to:", csv_files)

# Load selected CSV + auto-fix phones
try:
    df = pd.read_csv(selected_csv)
    df.columns = df.columns.str.strip()
    
    def fix_phone(p):
        p = str(p).strip()
        if not p.startswith("+"):
            return "+1" + p.lstrip("1")
        return p
    
    df["phone"] = df["phone"].apply(fix_phone)
    
    st.success(f"✅ Loaded {len(df)} employees from **{selected_csv}**")
except Exception as e:
    st.error(f"Could not load {selected_csv}: {e}")
    st.stop()

# Message
message = st.text_area("Message to send to all employees:", height=150,
                       placeholder="All hands: Network maintenance tonight at 10 PM...")

if st.button("🚀 SEND TO ALL EMPLOYEES", type="primary", use_container_width=True):
    if not message.strip():
        st.error("Message cannot be empty!")
    else:
        with st.spinner(f"Sending to {len(df)} employees as {username}..."):
            success_count = 0
            for _, row in df.iterrows():
                try:
                    client.messages.create(
                        messaging_service_sid=service_sid,
                        body=message,
                        to=row["phone"]
                    )
                    success_count += 1
                except Exception as e:
                    st.warning(f"Failed {row.get('name', row['phone'])}: {e}")

            # Log
            log_entry = pd.DataFrame([{
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "sender": username,
                "csv_used": selected_csv,
                "message": message,
                "recipients": len(df),
                "successful": success_count
            }])
            
            log_file = "broadcast_log.csv"
            if os.path.exists(log_file):
                log_entry.to_csv(log_file, mode='a', header=False, index=False)
            else:
                log_entry.to_csv(log_file, index=False)

            st.success(f"✅ Sent to {success_count}/{len(df)} employees!")
            st.info("Broadcast logged.")

st.divider()
st.caption("Note: Campaign is currently under Twilio review. Messages will deliver once approved.")
