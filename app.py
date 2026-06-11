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

    # Upload new list
    st.subheader("📤 Upload New Employee List")
    uploaded_file = st.file_uploader("Upload CSV (columns: name, phone)", type=["csv"])
    if uploaded_file:
        try:
            new_df = pd.read_csv(uploaded_file)
            filename = uploaded_file.name
            if not filename.endswith(".csv"):
                filename += ".csv"
            new_df.to_csv(filename, index=False)
            st.success(f"✅ Saved as **{filename}**")
        except Exception as e:
            st.error(f"Upload failed: {e}")

    # Select existing list
    csv_files = [f for f in os.listdir(".") if f.endswith(".csv")]
    csv_files.sort()
    if not csv_files:
        st.error("No CSV files found. Please upload one above.")
        st.stop()

    selected_csv = st.selectbox("Select employee list to send to:", csv_files)

    # Load with robust cleaning
    try:
        df = pd.read_csv(selected_csv)
        df.columns = df.columns.str.strip()
        
        col_map = {col.lower(): col for col in df.columns}
        phone_col = col_map.get('phone')
        name_col = col_map.get('name', df.columns[0])

        def fix_phone(p):
            if pd.isna(p) or str(p).strip() == "":
                return None
            p = str(p).strip()
            # Keep only digits
            digits = ''.join(filter(str.isdigit, p))
            # Remove leading 1 if 11 digits
            if len(digits) == 11 and digits.startswith('1'):
                digits = digits[1:]
            # Must be exactly 10 digits
            if len(digits) == 10:
                return "+1" + digits
            return None

        df["phone"] = df[phone_col].apply(fix_phone)
        original_count = len(df)
        df = df.dropna(subset=["phone"]).reset_index(drop=True)
        
        st.success(f"✅ Loaded {len(df)} valid recipients (out of {original_count}) from **{selected_csv}**")
    except Exception as e:
        st.error(f"Could not load {selected_csv}: {e}")
        st.stop()

    username = st.text_input("Your name (for logging):", placeholder="Enter your full name")
    message = st.text_area("Message to send:", height=150, placeholder="All hands: Network maintenance tonight at 10 PM...")

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

                st.success(f"✅ Sent to {success_count}/{len(df)} employees!")
                st.info("Broadcast logged.")

    st.caption("Note: Campaign is currently under Twilio review.")

# ====================== VIEW PAST BROADCASTS ======================
with tab2:
    st.title("📜 Past Broadcasts")
    if os.path.exists("broadcast_log.csv"):
        log_df = pd.read_csv("broadcast_log.csv")
        st.dataframe(log_df.sort_values("timestamp", ascending=False), use_container_width=True)
        st.download_button("📥 Download full log", log_df.to_csv(index=False), "broadcast_log.csv", "text/csv")
    else:
        st.info("No broadcasts yet.")
