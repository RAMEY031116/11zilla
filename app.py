# import streamlit as st
# import pandas as pd
# import gspread
# from datetime import datetime

# # 🏠 Set up the app layout and title
# st.set_page_config(page_title="Flatmate Manager", page_icon="🏠", layout="centered")
# st.title("🏠 Flatmate Expense & Message Board")

# # ---------------- Google Sheets Setup ----------------
# def connect_to_google_sheets():
#     """Connect to Google Sheets using credentials stored in Streamlit secrets."""
#     try:
#         creds = st.secrets["gcp_service_account"]
#         sheet_id = st.secrets["sheet_id"]
#         client = gspread.service_account_from_dict(creds)
#         return client.open_by_key(sheet_id)
#     except KeyError:
#         st.error("Missing Google Sheets credentials or sheet ID in secrets.")
#         st.stop()

# def setup_worksheets(sheet):
#     """Ensure all required worksheets exist and have correct headers."""
#     required = {
#         "expenses": ["timestamp", "paid_by", "description", "category", "amount", "settled"],
#         "announcements": ["timestamp", "author", "message"],
#         "flatmates": ["name"],
#         "archive": ["timestamp", "paid_by", "description", "category", "amount", "settled"]
#     }

#     existing = {ws.title for ws in sheet.worksheets()}
#     for name, headers in required.items():
#         if name not in existing:
#             ws = sheet.add_worksheet(title=name, rows=1000, cols=len(headers))
#             ws.update([headers])

#     # Seed default flatmates if empty
#     flatmate_ws = sheet.worksheet("flatmates")
#     if not flatmate_ws.get_all_records():
#         for name in ["You", "Flatmate 1", "Flatmate 2"]:
#             flatmate_ws.append_row([name])

# # ---------------- Data Helpers ----------------
# def load_sheet_data(ws, headers):
#     """Load data from a worksheet into a DataFrame with guaranteed headers."""
#     records = ws.get_all_records()
#     return pd.DataFrame(records) if records else pd.DataFrame(columns=headers)

# def save_df_to_sheet(ws, df, headers):
#     """Save a DataFrame back to a worksheet."""
#     ws.clear()
#     ws.update([headers])
#     if not df.empty:
#         values = df.astype(str).replace("nan", "").values.tolist()
#         ws.update("A2", values)

# def load_all_data(sheet):
#     """Load all worksheets into DataFrames."""
#     expenses = load_sheet_data(sheet.worksheet("expenses"), ["timestamp", "paid_by", "description", "category", "amount", "settled"])
#     announcements = load_sheet_data(sheet.worksheet("announcements"), ["timestamp", "author", "message"])
#     flatmates = load_sheet_data(sheet.worksheet("flatmates"), ["name"])

#     # Clean up expenses
#     if not expenses.empty:
#         expenses["amount"] = pd.to_numeric(expenses["amount"], errors="coerce").fillna(0.0)
#         expenses["settled"] = expenses["settled"].astype(str).str.lower().isin(["true", "1", "yes"])

#     return expenses, announcements, flatmates

# def calculate_balances(expenses, flatmate_names):
#     """Calculate how much each flatmate owes or is owed."""
#     unsettled = expenses[~expenses["settled"]]
#     total = unsettled["amount"].sum()
#     per_person = total / max(len(flatmate_names), 1)
#     paid = unsettled.groupby("paid_by")["amount"].sum()

#     balances = []
#     for name in flatmate_names:
#         paid_amount = paid.get(name, 0.0)
#         balance = round(paid_amount - per_person, 2)
#         balances.append({
#             "name": name,
#             "paid": round(paid_amount, 2),
#             "share": round(per_person, 2),
#             "balance": balance
#         })

#     return pd.DataFrame(balances).sort_values("balance", ascending=False)

# # ---------------- Load and Prepare ----------------
# sheet = connect_to_google_sheets()
# setup_worksheets(sheet)
# expenses_df, announcements_df, flatmates_df = load_all_data(sheet)
# flatmate_names = flatmates_df["name"].tolist()

# # ---------------- Sidebar Navigation ----------------
# page = st.sidebar.radio("Choose a page", [
#     "Dashboard", "Add Expense", "Edit Expenses", "Announcements", "Manage Flatmates", "Help"
# ])

# # ---------------- Dashboard ----------------
# if page == "Dashboard":
#     st.subheader("📊 Current Balances")
#     st.dataframe(calculate_balances(expenses_df, flatmate_names), use_container_width=True)

#     st.subheader("🧾 Recent Expenses")
#     if not expenses_df.empty:
#         st.dataframe(expenses_df.sort_values("timestamp", ascending=False).head(10), use_container_width=True)
#     else:
#         st.info("No expenses yet.")

#     st.subheader("📢 Latest Announcements")
#     if "timestamp" in announcements_df.columns and not announcements_df.empty:
#         for _, row in announcements_df.sort_values("timestamp", ascending=False).head(5).iterrows():
#             st.markdown(f"**{row['author']}** — {row['message']}  \n*{row['timestamp']}*")
#     else:
#         st.info("No announcements yet.")

# # ---------------- Add Expense ----------------
# elif page == "Add Expense":
#     st.subheader("➕ Add Expense")
#     with st.form("expense_form", clear_on_submit=True):
#         who_paid = st.selectbox("Who paid?", flatmate_names)
#         description = st.text_input("Description")
#         category = st.selectbox("Category", ["Groceries", "Bills", "Transport", "Fun", "Other"])
#         amount = st.number_input("Amount (£)", min_value=0.0, step=0.5)
#         submit = st.form_submit_button("Add")

#     if submit:
#         if amount > 0 and description.strip():
#             timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#             sheet.worksheet("expenses").append_row([timestamp, who_paid, description, category, amount, False])
#             st.success("Expense added!")
#         else:
#             st.warning("Please enter a valid description and amount.")

# # ---------------- Edit Expenses ----------------
# elif page == "Edit Expenses":
#     st.subheader("✏️ Edit Expenses")
#     if expenses_df.empty:
#         st.info("No expenses to edit.")
#     else:
#         edited = st.data_editor(expenses_df, num_rows="dynamic", use_container_width=True)
#         col1, col2, col3 = st.columns(3)

#         if col1.button("💾 Save"):
#             save_df_to_sheet(sheet.worksheet("expenses"), edited, expenses_df.columns.tolist())
#             st.success("Changes saved.")

#         if col2.button("🗄️ Archive Settled"):
#             settled = edited[edited["settled"] == True]
#             remaining = edited[edited["settled"] == False]
#             archive_ws = sheet.worksheet("archive")
#             for _, row in settled.iterrows():
#                 archive_ws.append_row(row.tolist())
#             save_df_to_sheet(sheet.worksheet("expenses"), remaining, expenses_df.columns.tolist())
#             st.success(f"Archived {len(settled)} rows.")

#         if col3.button("🧹 Mark All Settled"):
#             edited["settled"] = True
#             save_df_to_sheet(sheet.worksheet("expenses"), edited, expenses_df.columns.tolist())
#             st.success("All marked as settled.")

# # ---------------- Announcements ----------------
# elif page == "Announcements":
#     st.subheader("📢 Post Announcement")
#     with st.form("announcement_form", clear_on_submit=True):
#         author = st.selectbox("Author", flatmate_names)
#         message = st.text_area("Message")
#         post = st.form_submit_button("Post")

#     if post and message.strip():
#         timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         sheet.worksheet("announcements").append_row([timestamp, author, message])
#         st.success("Announcement posted.")
#     elif post:
#         st.warning("Message cannot be empty.")

#     st.subheader("📝 Recent Announcements")
#     if "timestamp" in announcements_df.columns and not announcements_df.empty:
#         for _, row in announcements_df.sort_values("timestamp", ascending=False).iterrows():
#             st.markdown(f"**{row['author']}** — {row['message']}  \n*{row['timestamp']}*")
#     else:
#         st.info("No announcements yet.")

# # ---------------- Manage Flatmates ----------------
# elif page == "Manage Flatmates":
#     st.subheader("👥 Manage Flatmates")
#     edited = st.data_editor(flatmates_df, num_rows="dynamic", use_container_width=True)
#     if st.button("💾 Save Flatmates"):
#         cleaned = edited[edited["name"].astype(str).str.strip() != ""]
#         if cleaned.empty:
#             st.warning("At least one name is required.")
#         else:
#             save_df_to_sheet(sheet.worksheet("flatmates"), cleaned, ["name"])
#             st.success("Flatmates updated.")

# # ---------------- Help ----------------


import streamlit as st
import gspread
from datetime import datetime

# ----------------- App Title -----------------
st.title("💸 Add Expense")

# ----------------- Connect to Google Sheets -----------------
# This uses your Streamlit secrets: "gcp_service_account" and "sheet_id"
sheet = gspread.service_account_from_dict(st.secrets["gcp_service_account"]) \
                  .open_by_key(st.secrets["sheet_id"]) \
                  .worksheet("expenses")

# ----------------- Expense Form -----------------
st.subheader("Enter your expense:")

# Input fields
who_paid = st.text_input("Who paid?")
description = st.text_input("Description")
amount = st.number_input("Amount (£)", min_value=0.0, step=0.5)

# Button to submit
if st.button("Add Expense"):
    if who_paid and description and amount > 0:
        # Get current time
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Add a new row to Google Sheets
        sheet.append_row([timestamp, who_paid, description, amount])
        st.success(f"✅ Added: {who_paid} paid £{amount} for {description}")
    else:
        st.warning("Please fill in all fields and enter a valid amount.")


