import streamlit as st
import pandas as pd
import os

# --- PAGE CONFIGURATION & PREMIUM THEME ---
st.set_page_config(page_title="FinTrack Premium", page_icon="🏦", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .css-1r6slb0, .css-12oz5g7 { padding: 2rem 2rem; border-radius: 15px; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    div[data-testid="metric-container"] { background-color: #ffffff; border: 1px solid #e0e4e8; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { padding: 10px 20px; border-radius: 5px 5px 0 0; background-color: #eef2f5; }
    .stTabs [aria-selected="true"] { background-color: #ffffff; border-bottom: 3px solid #1f77b4; }
    </style>
""", unsafe_allow_html=True)

from form_tab import render_form_tab
from funds_tab import render_funds_tab
from service_tab import render_service_tab

# ==========================================
# FIX: Added "Org Name" to match your form
# ==========================================
CSV_FILE = "data.csv"
if not os.path.exists(CSV_FILE):
    df = pd.DataFrame(columns=[
        "Date", "Transaction Type", "Currency", "Payment Status", "Amount", 
        "Frequency", "Payment App", "Phone Number", "Bank Name", 
        "Person/Org Name", "Org Name", "Domain", "Sub-Category", 
        "Description", "Extra Details"
    ])
    df.to_csv(CSV_FILE, index=False)

st.title("🏦 Asset & Finance Portfolio")

main_tabs = st.tabs(["📝 Data Entry Form", "📈 Funds Dashboard", "🛠️ Service"])

with main_tabs[0]: render_form_tab(CSV_FILE)
with main_tabs[1]: render_funds_tab(CSV_FILE)
with main_tabs[2]: render_service_tab()
