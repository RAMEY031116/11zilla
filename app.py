import streamlit as st
import gspread
from datetime import datetime

st.title("11zilla expense app")

# Connect to Google Sheet
sheet = gspread.service_account_from_dict(st.secrets["gcp_service_account"]) \
                  .open_by_key(st.secrets["sheet_id"]) \
                  .worksheet("expenses")

# Form to add an expense
who = st.text_input("Who paid?")
desc = st.text_input("Description")
amount = st.number_input("Amount (£)", min_value=0.0, step=0.5, format="%.2f") 

if st.button("Add Expense"):
    if who and desc and amount > 0:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([ts, who, desc, float(amount)])  
        st.success(f"Added: {who} paid £{amount:.2f} for {desc}")
    else:
        st.warning("Please fill all fields correctly.")

st.title("shows costs")

st.write("this will list the indivisual costs")

sheet = gspread.service_account_from_dict(st.secrets["gcp_service_account"]) \
                  .open_by_key(st.secrets["sheet_id"]) \
                  .worksheet("flatmates")


flatmates = sheet.col_values(1)[1:]

for x in flatmates:
    st.write(x)