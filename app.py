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
PASSWORD = st.secrets["PASSWORD"]   # ← Put your strong random password here

# ====================== AUTH ======================
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

# ====================== NAVIGATION ======================
tab1, tab2 = st.tabs(["🚀 Send Alert", "📜 View Past Broadcasts"])

# ====================== SEND ALERT TAB ======================
with tab1:
    st.title("Send Company-Wide Alert")
    st.caption("IT & HR SMS Broadcast Tool • Powered by Twilio")

    # === UPLOAD NEW LIST ===
    st.subheader("📤 Upload New Employee List")
    uploaded_file = st.file_uploader("Upload CSV (must have 'name' and 'phone' columns)", 
                                   type=["csv"])
    if uploaded_file:
        try:
            new_df = pd.read_csv(uploaded_file)
            filename = uploaded_file.name
            if not filename.endswith(".csv"):
                filename += ".csv"
            new_df.to_csv(filename, index=False)
            st.success(f"✅ Uploaded and saved as **{filename}**")
        except Exception as e:
            st.error(f"Upload failed: {e}")

    # === SELECT EXISTING LIST ===
    csv_files = [f for f in os.listdir(".") if f.endswith(".csv")]
    csv_files.sort()
    
    if not csv_files:
        st.error("No CSV files found. Please upload one above.")
        st.stop()

    selected_csv = st.selectbox("Select employee list to send to:", csv_files)

    # Load selected CSV
    try:
        df = pd.read_csv(selected_csv)
        df.columns = df.columns.str.strip().str.lower()
        
        if 'phone' not in df.columns:
            st.error("CSV must have a 'phone' column")
            st.stop()
        
        def fix_phone(p):
            p = str(p).strip()
            if not p.startswith("+"):
                return "+1" + p.lstrip("1")
            return p
        
        df["phone"] = df["phone"].apply(fix_phone)
        
        name_col = 'name' if 'name' in df.columns else df.columns[0]
        st.success(f"✅ Loaded {len(df)} recipients from **{selected_csv}**")
    except Exception as e:
        st.error(f"Could not load {selected_csv}: {e}")
        st.stop()

    # Username + Message
    username = st.text_input("Your name (for logging):", value="", placeholder="Enter your full name")
    message = st.text_area("Message to send:", height=150, 
                          placeholder="All hands: Network maintenance tonight at 10 PM...")

    if st.button("🚀 SEND TO ALL EMPLOYEES", type="primary", use_container_width=True):
        if not username.strip():
            st.error("Please enter your name.")
        elif not message.strip():
            st.error("Message cannot be empty!")
        else:
            with st.spinner(f"Sending to {len(df)} employees..."):
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
                        st.warning(f"Failed {row.get(name_col, row['phone'])}: {e}")

                # Log
                log_entry = pd.DataFrame([{
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "sender": username.strip(),
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

                st.success(f"✅ Message sent to {success_count}/{len(df)} employees!")
                st.info("Broadcast logged.")

    st.caption("Note: Campaign is currently under Twilio review.")

# ====================== VIEW PAST BROADCASTS ======================
with tab2:
    st.title("📜 Past Broadcasts")
    if os.path.exists("broadcast_log.csv"):
        log_df = pd.read_csv("broadcast_log.csv")
        st.dataframe(log_df.sort_values("timestamp", ascending=False), use_container_width=True)
        st.download_button("Download Log", log_df.to_csv(index=False), "broadcast_log.csv", "text/csv")
    else:
        st.info("No broadcasts yet.")
