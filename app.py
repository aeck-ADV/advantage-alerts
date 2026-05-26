import streamlit as st
import pandas as pd
import os
from datetime import datetime
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

# ====================== CONFIG ======================
PASSWORD = "AdvanT&ge2975%201"          # ← CHANGE THIS
LOG_FILE = "broadcast_log.csv"

# Twilio setup
client = Client(
    os.getenv("TWILIO_API_KEY_SID"),
    os.getenv("TWILIO_API_KEY_SECRET"),
    os.getenv("TWILIO_ACCOUNT_SID")
)
service_sid = os.getenv("TWILIO_MESSAGING_SERVICE_SID")

# ====================== PASSWORD ======================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("📢 Advantage Investigations Alert")
    password = st.text_input("Enter password:", type="password")
    if st.button("Login"):
        if password == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")
    st.stop()

# ====================== SIDEBAR NAVIGATION ======================
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["Send Alert", "View Past Broadcasts"])

# ====================== SEND ALERT PAGE ======================
if page == "Send Alert":
    st.title("🚀 Send Company-Wide Alert")
    st.caption("IT & HR SMS Broadcast Tool • Powered by Twilio")

    # Load employees + auto-fix phones
    try:
        df = pd.read_csv("employees.csv")
        df.columns = df.columns.str.strip()
        def fix_phone(p):
            p = str(p).strip()
            if not p.startswith("+"):
                return "+1" + p.lstrip("1")
            return p
        df["phone"] = df["phone"].apply(fix_phone)
        st.success(f"✅ Loaded {len(df)} employees")
    except Exception as e:
        st.error(f"Could not load employees.csv: {e}")
        st.stop()

    message = st.text_area("Message to send to all employees:", height=150,
                           placeholder="All hands: Network maintenance tonight at 10 PM...")
    sender_name = st.text_input("Your name (for logging):", value="IT/HR User")

    if st.button("🚀 SEND TO ALL EMPLOYEES", type="primary", use_container_width=True):
        if not message.strip():
            st.error("Message cannot be empty!")
        else:
            with st.spinner("Sending..."):
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

                # Log the broadcast
                log_entry = pd.DataFrame([{
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "sender": sender_name,
                    "message": message,
                    "recipients": len(df),
                    "successful": success_count
                }])
                if os.path.exists(LOG_FILE):
                    log_entry.to_csv(LOG_FILE, mode='a', header=False, index=False)
                else:
                    log_entry.to_csv(LOG_FILE, index=False)

                st.success(f"✅ Sent to {success_count}/{len(df)} employees!")
                st.info("Broadcast logged.")

    st.caption("Note: Campaign is currently under Twilio review. Messages will deliver once approved.")

# ====================== VIEW PAST BROADCASTS PAGE ======================
else:
    st.title("📜 Past Broadcasts")
    st.caption("All previous company-wide alerts")

    if os.path.exists(LOG_FILE):
        log_df = pd.read_csv(LOG_FILE)
        st.dataframe(log_df.sort_values("timestamp", ascending=False), use_container_width=True)
        
        st.download_button(
            label="📥 Download full log as CSV",
            data=log_df.to_csv(index=False),
            file_name="broadcast_log.csv",
            mime="text/csv"
        )
    else:
        st.info("No broadcasts yet. Send your first one to see the log here.")

    st.caption("Note: Campaign is currently under Twilio review. Messages will deliver once approved.")