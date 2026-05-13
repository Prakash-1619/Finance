import streamlit as st
import pandas as pd
import os

# Page config must be the first Streamlit command
st.set_page_config(page_title="Asset & Finance Tracker", page_icon="📊", layout="wide")

# Import your tab modules
from form_tab import render_form_tab
from funds_tab import render_funds_tab
from service_tab import render_service_tab

# Initialize the CSV database if it doesn't exist
CSV_FILE = "data.csv"
if not os.path.exists(CSV_FILE):
    df = pd.DataFrame(columns=[
        "Date", "Transaction Type", "Domain", "Category", 
        "Amount", "Payment Method", "Description", "Extra Details"
    ])
    df.to_csv(CSV_FILE, index=False)

st.title("📊 Asset & Finance Tracker")

# Create Tabs
tab1, tab2, tab3 = st.tabs(["📝 Data Entry Form", "📈 Funds & Balance Sheet", "🛠️ Service"])

with tab1:
    render_form_tab(CSV_FILE)

with tab2:
    render_funds_tab(CSV_FILE)

with tab3:
    render_service_tab()
