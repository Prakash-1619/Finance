import streamlit as st
import pandas as pd

from form_tab import render_form_tab
from funds_tab import render_funds_tab
from service_tab import render_service_tab
from github_sync import load_data

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

PROFILE_OPTIONS = [
    "Universal Finance",
    "Personal Finance",
    "Farm & Livestock",
    "Credit & Loans",
    "Compact Overview"
]

with st.sidebar:
    st.title("FinTrack Premium")
    st.markdown("""
    ## Customizable layout
    Choose the flow that best matches your financial needs.
    """)
    st.divider()

    selected_profile = st.selectbox("Select layout profile", PROFILE_OPTIONS, index=0)
    preferred_domains = st.multiselect(
        "Preferred finance domains",
        ["Loans", "EMI", "Car", "Cows", "Sheep", "Agri Land", "Home", "Personal", "Friends lending", "Miscellaneous"],
        default=[]
    )
    compact_mode = st.checkbox("Enable compact dashboard layout", value=False)
    show_service_tab = st.checkbox("Show Service tab", value=True)

    df_summary = load_data()
    if df_summary.empty:
        st.info("No transaction data available yet. Add a record in Data Entry.")
    else:
        total_income = df_summary[df_summary['Transaction Type'].isin(['Income', 'Received'])]['Amount'].sum()
        total_expenditure = df_summary[df_summary['Transaction Type'].isin(['Expenditure', 'Paid'])]['Amount'].sum()
        st.metric("Records", len(df_summary))
        st.metric("Net Balance", f"₹{total_income - total_expenditure:,.2f}")
        last_date = pd.to_datetime(df_summary['Date']).max().date()
        st.metric("Last Entry", last_date)

st.title("🏦 Asset & Financial Management Dashboard")
st.caption("Capture transactions, review performance, and manage services from one place.")

main_tabs = ["📊 Dashboard", "📝 Data Entry Form"]
if show_service_tab:
    main_tabs.append("🛠️ Service")

tabs = st.tabs(main_tabs)

with tabs[0]:
    render_funds_tab(profile=selected_profile, preferred_domains=preferred_domains, compact=compact_mode)
with tabs[1]:
    render_form_tab()
if show_service_tab:
    with tabs[2]:
        render_service_tab()
