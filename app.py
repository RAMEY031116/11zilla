# import streamlit as st
# import pandas as pd
# import gspread
# from datetime import datetime

# st.set_page_config(page_title="Flatmate Manager", page_icon="🏠", layout="centered")

# # ---------------- Helpers: Google Sheets ----------------
# def get_client():
#     try:
#         return gspread.service_account_from_dict(st.secrets["gcp_service_account"])
#     except KeyError:
#         st.error("Missing gcp_service_account in Streamlit secrets. Add it via Settings → Secrets or .streamlit/secrets.toml locally.")
#         st.stop()

# def get_spreadsheet(client):
#     try:
#         sheet_id = st.secrets["sheet_id"]
#     except KeyError:
#         st.error("Missing 'sheet_id' in Streamlit secrets.")
#         st.stop()
#     return client.open_by_key(sheet_id)

# def ensure_worksheets(ss):
#     needed = {
#         "expenses": ["timestamp","paid_by","description","category","amount","settled"],
#         "announcements": ["timestamp","author","message"],
#         "flatmates": ["name"],
#         "archive": ["timestamp","paid_by","description","category","amount","settled"]
#     }
#     existing = {ws.title for ws in ss.worksheets()}
#     for title, headers in needed.items():
#         if title not in existing:
#             ws = ss.add_worksheet(title, rows=1000, cols=len(headers))
#             ws.update([headers])

#     # Seed default flatmates if empty
#     fm_ws = ss.worksheet("flatmates")
#     fm_data = fm_ws.get_all_records()
#     if not fm_data:
#         fm_ws.append_row(["You"])
#         fm_ws.append_row(["Flatmate 1"])
#         fm_ws.append_row(["Flatmate 2"])

# def ws_to_df(ws, headers=None):
#     records = ws.get_all_records()
#     df = pd.DataFrame(records)
#     if headers and df.empty:
#         df = pd.DataFrame(columns=headers)
#     return df

# def df_to_ws(ws, df, headers):
#     ws.clear()
#     ws.update([headers])
#     if not df.empty:
#         values = df.astype(object).where(pd.notnull(df), "").values.tolist()
#         ws.update(range_name=f"A2", values=values)

# # ---------------- Load data ----------------
# gc = get_client()
# ss = get_spreadsheet(gc)
# ensure_worksheets(ss)

# ws_exp = ss.worksheet("expenses")
# ws_ann = ss.worksheet("announcements")
# ws_fm = ss.worksheet("flatmates")
# ws_arc = ss.worksheet("archive")

# expenses_cols = ["timestamp","paid_by","description","category","amount","settled"]
# ann_cols = ["timestamp","author","message"]
# flatmates_cols = ["name"]

# def load_data():
#     exp = ws_to_df(ws_exp, expenses_cols)
#     ann = ws_to_df(ws_ann, ann_cols)
#     fm = ws_to_df(ws_fm, flatmates_cols)
#     if not exp.empty:
#         exp["amount"] = pd.to_numeric(exp["amount"], errors="coerce").fillna(0.0)
#         exp["settled"] = exp["settled"].astype(str).str.lower().isin(["true","1","yes"])
#     return exp, ann, fm

# def compute_balances(expenses, flatmates):
#     flatmates = [x for x in flatmates if isinstance(x, str) and x.strip()]
#     if not flatmates:
#         return pd.DataFrame(columns=["name","paid","share","balance"])
#     unsettled = expenses[~expenses["settled"]] if not expenses.empty else expenses
#     total = unsettled["amount"].sum() if not unsettled.empty else 0.0
#     per_head = total / max(len(flatmates), 1)
#     paid = unsettled.groupby("paid_by")["amount"].sum() if not unsettled.empty else pd.Series(dtype=float)
#     rows = []
#     for name in flatmates:
#         p = float(paid.get(name, 0.0))
#         rows.append({"name": name, "paid": round(p,2), "share": round(per_head,2), "balance": round(p - per_head, 2)})
#     df = pd.DataFrame(rows)
#     return df.sort_values("balance", ascending=False)

# # ---------------- UI ----------------
# st.title("🏠 Flatmate Expense & Message Board")
# page = st.sidebar.radio("Go to", ["Dashboard","Add Expense","Edit Expenses","Announcements","Manage Flatmates","Help"])

# exp_df, ann_df, fm_df = load_data()
# flatmates = fm_df["name"].tolist() if not fm_df.empty else ["You","Flatmate 1","Flatmate 2"]

# # ---------------- Dashboard ----------------
# if page == "Dashboard":
#     st.subheader("📊 Balances (Unsettled)")
#     bal_df = compute_balances(exp_df, flatmates)
#     st.dataframe(bal_df, use_container_width=True)

#     if not exp_df.empty:
#         st.subheader("🧾 Recent Expenses")
#         st.dataframe(exp_df.sort_values("timestamp", ascending=False).head(10), use_container_width=True)
#     else:
#         st.info("No expenses yet. Add your first one from the sidebar.")

#     if not ann_df.empty:
#         st.subheader("📢 Latest Announcements")
#         for _, row in ann_df.sort_values("timestamp", ascending=False).head(5).iterrows():
#             st.write(f"**{row['author']}** — {row['message']}  \n*{row['timestamp']}*")
#     else:
#         st.info("No announcements yet. Post one on the Announcements page.")

# # ---------------- Add Expense ----------------
# elif page == "Add Expense":
#     st.subheader("➕ Add a new expense")
#     with st.form("add_expense_form", clear_on_submit=True):
#         payer = st.selectbox("Who paid?", flatmates, index=0)
#         desc = st.text_input("Description (e.g., Tesco, Electricity top-up)")
#         cat = st.selectbox("Category", ["Groceries","Bills","Transport","Fun","Other"], index=0)
#         amount = st.number_input("Amount (£)", min_value=0.0, step=0.50, format="%.2f")
#         submitted = st.form_submit_button("Add expense")
#     if submitted:
#         if amount <= 0 or not desc.strip():
#             st.warning("Please enter a description and amount greater than 0.")
#         else:
#             ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#             ws_exp.append_row([ts, payer, desc.strip(), cat, float(amount), False], value_input_option="USER_ENTERED")
#             st.success("Expense added! Open the Dashboard to see balances.")

# # ---------------- Edit Expenses ----------------
# elif page == "Edit Expenses":
#     st.subheader("✏️ Edit expenses (toggle 'settled' to clear debts)")
#     editable = exp_df.copy()
#     if editable.empty:
#         st.info("No expenses yet.")
#     else:
#         editable = editable[expenses_cols]  # enforce column order
#         edited_df = st.data_editor(editable, num_rows="dynamic", use_container_width=True,
#                                    column_config={
#                                        "timestamp": st.column_config.TextColumn(disabled=True),
#                                        "amount": st.column_config.NumberColumn(step=0.01, format="£%.2f"),
#                                        "settled": st.column_config.CheckboxColumn()
#                                    })
#         col1, col2, col3 = st.columns(3)
#         if col1.button("💾 Save changes"):
#             df_to_ws(ws_exp, edited_df, expenses_cols)
#             st.success("Saved changes.")
#         if col2.button("🗄️ Archive settled rows"):
#             to_archive = edited_df[edited_df["settled"] == True].copy()
#             keep = edited_df[edited_df["settled"] == False].copy()
#             if not to_archive.empty:
#                 for _, r in to_archive.iterrows():
#                     ws_arc.append_row([r[c] for c in expenses_cols], value_input_option="USER_ENTERED")
#             df_to_ws(ws_exp, keep, expenses_cols)
#             st.success(f"Archived {len(to_archive)} settled rows.")
#         if col3.button("🧹 Mark ALL as settled"):
#             edited_df["settled"] = True
#             df_to_ws(ws_exp, edited_df, expenses_cols)
#             st.success("All rows marked as settled.")

# # ---------------- Announcements ----------------
# elif page == "Announcements":
#     st.subheader("📢 Post an announcement")
#     with st.form("ann_form", clear_on_submit=True):
#         author = st.selectbox("From", flatmates, index=0)
#         msg = st.text_area("Message", placeholder="e.g., Today is chicken biryani for dinner!")
#         post = st.form_submit_button("Post")
#     if post:
#         if msg.strip():
#             ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#             ws_ann.append_row([ts, author, msg.strip()], value_input_option="USER_ENTERED")
#             st.success("Posted!")
#         else:
#             st.warning("Please write a message before posting.")

#     st.subheader("📝 Recent")
#     if ann_df.empty:
#         st.info("No announcements yet.")
#     else:
#         for _, row in ann_df.sort_values("timestamp", ascending=False).iterrows():
#             st.write(f"**{row['author']}** — {row['message']}  \n*{row['timestamp']}*")

# # ---------------- Manage Flatmates ----------------
# elif page == "Manage Flatmates":
#     st.subheader("👥 Add / remove flatmates")
#     current = fm_df.copy()
#     edited = st.data_editor(current, num_rows="dynamic", use_container_width=True,
#                             column_config={"name": st.column_config.TextColumn()})
#     if st.button("💾 Save flatmates"):
#         edited = edited[edited["name"].astype(str).str.strip() != ""]
#         if edited.empty:
#             st.warning("At least one name is required.")
#         else:
#             df_to_ws(ws_fm, edited, ["name"])
#             st.success("Saved names.")

#     st.caption("Tip: Balances split evenly across the people listed here.")
# # ---------------- Help ----------------
# # ---------------- Help ----------------
# else:
#     st.subheader("🆘 How this works (quick guide)")
#     st.markdown("""
# **Basics**
# - Add expenses on *Add Expense*.
# - Balances on *Dashboard* show who owes who. Positive balance = person is **owed** money.
# - Toggle **settled** on *Edit Expenses* when someone pays back. You can archive settled rows.

# **Sharing**
# - This app uses a shared Google Sheet (your **sheet_id**) so everyone sees the same data.
# - Give *Editor* access to the service account email found in your secrets.

# **Safety**
# - Credentials are stored in Streamlit **Secrets**, not in your code/repo.
# """)

import streamlit as st
import pandas as pd
import gspread
from datetime import datetime

# 🏠 Set up the app layout and title
st.set_page_config(page_title="Flatmate Manager", page_icon="🏠", layout="centered")
st.title("🏠 Flatmate Expense & Message Board")

# ---------------- Google Sheets Setup ----------------
def connect_to_google_sheets():
    """Connect to Google Sheets using credentials stored in Streamlit secrets."""
    try:
        creds = st.secrets["gcp_service_account"]
        sheet_id = st.secrets["sheet_id"]
        client = gspread.service_account_from_dict(creds)
        return client.open_by_key(sheet_id)
    except KeyError:
        st.error("Missing Google Sheets credentials or sheet ID in secrets.")
        st.stop()

def setup_worksheets(sheet):
    """Ensure all required worksheets exist and have correct headers."""
    required = {
        "expenses": ["timestamp", "paid_by", "description", "category", "amount", "settled"],
        "announcements": ["timestamp", "author", "message"],
        "flatmates": ["name"],
        "archive": ["timestamp", "paid_by", "description", "category", "amount", "settled"]
    }

    existing = {ws.title for ws in sheet.worksheets()}
    for name, headers in required.items():
        if name not in existing:
            ws = sheet.add_worksheet(title=name, rows=1000, cols=len(headers))
            ws.update([headers])

    # Seed default flatmates if empty
    flatmate_ws = sheet.worksheet("flatmates")
    if not flatmate_ws.get_all_records():
        for name in ["You", "Flatmate 1", "Flatmate 2"]:
            flatmate_ws.append_row([name])

# ---------------- Data Helpers ----------------
def load_sheet_data(ws, headers):
    """Load data from a worksheet into a DataFrame with guaranteed headers."""
    records = ws.get_all_records()
    return pd.DataFrame(records) if records else pd.DataFrame(columns=headers)

def save_df_to_sheet(ws, df, headers):
    """Save a DataFrame back to a worksheet."""
    ws.clear()
    ws.update([headers])
    if not df.empty:
        values = df.astype(str).replace("nan", "").values.tolist()
        ws.update("A2", values)

def load_all_data(sheet):
    """Load all worksheets into DataFrames."""
    expenses = load_sheet_data(sheet.worksheet("expenses"), ["timestamp", "paid_by", "description", "category", "amount", "settled"])
    announcements = load_sheet_data(sheet.worksheet("announcements"), ["timestamp", "author", "message"])
    flatmates = load_sheet_data(sheet.worksheet("flatmates"), ["name"])

    # Clean up expenses
    if not expenses.empty:
        expenses["amount"] = pd.to_numeric(expenses["amount"], errors="coerce").fillna(0.0)
        expenses["settled"] = expenses["settled"].astype(str).str.lower().isin(["true", "1", "yes"])

    return expenses, announcements, flatmates

def calculate_balances(expenses, flatmate_names):
    """Calculate how much each flatmate owes or is owed."""
    unsettled = expenses[~expenses["settled"]]
    total = unsettled["amount"].sum()
    per_person = total / max(len(flatmate_names), 1)
    paid = unsettled.groupby("paid_by")["amount"].sum()

    balances = []
    for name in flatmate_names:
        paid_amount = paid.get(name, 0.0)
        balance = round(paid_amount - per_person, 2)
        balances.append({
            "name": name,
            "paid": round(paid_amount, 2),
            "share": round(per_person, 2),
            "balance": balance
        })

    return pd.DataFrame(balances).sort_values("balance", ascending=False)

# ---------------- Load and Prepare ----------------
sheet = connect_to_google_sheets()
setup_worksheets(sheet)
expenses_df, announcements_df, flatmates_df = load_all_data(sheet)
flatmate_names = flatmates_df["name"].tolist()

# ---------------- Sidebar Navigation ----------------
page = st.sidebar.radio("Choose a page", [
    "Dashboard", "Add Expense", "Edit Expenses", "Announcements", "Manage Flatmates", "Help"
])

# ---------------- Dashboard ----------------
if page == "Dashboard":
    st.subheader("📊 Current Balances")
    st.dataframe(calculate_balances(expenses_df, flatmate_names), use_container_width=True)

    st.subheader("🧾 Recent Expenses")
    if not expenses_df.empty:
        st.dataframe(expenses_df.sort_values("timestamp", ascending=False).head(10), use_container_width=True)
    else:
        st.info("No expenses yet.")

    st.subheader("📢 Latest Announcements")
    if "timestamp" in announcements_df.columns and not announcements_df.empty:
        for _, row in announcements_df.sort_values("timestamp", ascending=False).head(5).iterrows():
            st.markdown(f"**{row['author']}** — {row['message']}  \n*{row['timestamp']}*")
    else:
        st.info("No announcements yet.")

# ---------------- Add Expense ----------------
elif page == "Add Expense":
    st.subheader("➕ Add Expense")
    with st.form("expense_form", clear_on_submit=True):
        who_paid = st.selectbox("Who paid?", flatmate_names)
        description = st.text_input("Description")
        category = st.selectbox("Category", ["Groceries", "Bills", "Transport", "Fun", "Other"])
        amount = st.number_input("Amount (£)", min_value=0.0, step=0.5)
        submit = st.form_submit_button("Add")

    if submit:
        if amount > 0 and description.strip():
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sheet.worksheet("expenses").append_row([timestamp, who_paid, description, category, amount, False])
            st.success("Expense added!")
        else:
            st.warning("Please enter a valid description and amount.")

# ---------------- Edit Expenses ----------------
elif page == "Edit Expenses":
    st.subheader("✏️ Edit Expenses")
    if expenses_df.empty:
        st.info("No expenses to edit.")
    else:
        edited = st.data_editor(expenses_df, num_rows="dynamic", use_container_width=True)
        col1, col2, col3 = st.columns(3)

        if col1.button("💾 Save"):
            save_df_to_sheet(sheet.worksheet("expenses"), edited, expenses_df.columns.tolist())
            st.success("Changes saved.")

        if col2.button("🗄️ Archive Settled"):
            settled = edited[edited["settled"] == True]
            remaining = edited[edited["settled"] == False]
            archive_ws = sheet.worksheet("archive")
            for _, row in settled.iterrows():
                archive_ws.append_row(row.tolist())
            save_df_to_sheet(sheet.worksheet("expenses"), remaining, expenses_df.columns.tolist())
            st.success(f"Archived {len(settled)} rows.")

        if col3.button("🧹 Mark All Settled"):
            edited["settled"] = True
            save_df_to_sheet(sheet.worksheet("expenses"), edited, expenses_df.columns.tolist())
            st.success("All marked as settled.")

# ---------------- Announcements ----------------
elif page == "Announcements":
    st.subheader("📢 Post Announcement")
    with st.form("announcement_form", clear_on_submit=True):
        author = st.selectbox("Author", flatmate_names)
        message = st.text_area("Message")
        post = st.form_submit_button("Post")

    if post and message.strip():
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.worksheet("announcements").append_row([timestamp, author, message])
        st.success("Announcement posted.")
    elif post:
        st.warning("Message cannot be empty.")

    st.subheader("📝 Recent Announcements")
    if "timestamp" in announcements_df.columns and not announcements_df.empty:
        for _, row in announcements_df.sort_values("timestamp", ascending=False).iterrows():
            st.markdown(f"**{row['author']}** — {row['message']}  \n*{row['timestamp']}*")
    else:
        st.info("No announcements yet.")

# ---------------- Manage Flatmates ----------------
elif page == "Manage Flatmates":
    st.subheader("👥 Manage Flatmates")
    edited = st.data_editor(flatmates_df, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Save Flatmates"):
        cleaned = edited[edited["name"].astype(str).str.strip() != ""]
        if cleaned.empty:
            st.warning("At least one name is required.")
        else:
            save_df_to_sheet(sheet.worksheet("flatmates"), cleaned, ["name"])
            st.success("Flatmates updated.")

# ---------------- Help ----------------
else:
    st.subheader("🆘 How It Works")
    st.markdown("""
**Quick Guide**
- Add expenses and announcements using the sidebar.
-


