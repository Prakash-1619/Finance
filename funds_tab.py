import streamlit as st
import pandas as pd
import plotly.express as px
import json

# --- Helper: Flatten JSON for plotting ---
def get_clean_data(df):
    if df.empty:
        return df
    extras = df['Extra Details'].apply(lambda x: json.loads(x) if pd.notnull(x) and x != "" else {})
    extras_df = pd.json_normalize(extras)
    extras_df.index = df.index
    return pd.concat([df.drop(columns=['Extra Details']), extras_df], axis=1)

def render_funds_tab(csv_file):
    try:
        df = pd.read_csv(csv_file)
        if not df.empty:
            df['Date'] = pd.to_datetime(df['Date']).dt.date
    except Exception:
        st.error("⚠️ Data file not found. Please add an entry first.")
        return

    if df.empty:
        st.info("No records found yet.")
        return

    # --- TOP LEVEL DASHBOARD METRICS ---
    st.title("📉 Performance Dashboard")
    
    income = df[df['Transaction Type'] == 'Received']['Amount'].sum()
    expense = df[df['Transaction Type'] == 'Paid']['Amount'].sum()
    balance = income - expense

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Inflow", f"₹{income:,.2f}", delta_color="normal")
    with col2:
        st.metric("Total Outflow", f"₹{expense:,.2f}", delta="-", delta_color="inverse")
    with col3:
        st.metric("Net Balance", f"₹{balance:,.2f}", delta=f"{balance:,.2f}")

    st.divider()

    # --- TABS FOR DETAILED ANALYSIS ---
    tab_list = ["📊 Overall Analysis", "🚗 Car", "🐑 Sheep", "🌱 Agri Land", "🏠 Home", "🧍 Personal", "💸 Loans & EMI", "🤝 Friends"]
    tabs = st.tabs(tab_list)

    # --- TAB 1: OVERALL ANALYSIS ---
    with tabs[0]:
        st.subheader("Global Financial Trends")
        
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.write("**Expense Distribution by Domain**")
            exp_df = df[df['Transaction Type'] == 'Paid']
            fig_pie = px.pie(exp_df, values='Amount', names='Domain', hole=0.5, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with chart_col2:
            st.write("**Income vs Expense Over Time**")
            timeline = df.groupby(['Date', 'Transaction Type'])['Amount'].sum().reset_index()
            fig_line = px.line(timeline, x="Date", y="Amount", color="Transaction Type", markers=True)
            st.plotly_chart(fig_line, use_container_width=True)

        st.write("**All Transactions**")
        st.dataframe(df.sort_values('Date', ascending=False), use_container_width=True, hide_index=True)

    # --- GENERIC FUNCTION FOR SECTION DASHBOARDS ---
    def render_section_dashboard(domain_name, tab_obj):
        with tab_obj:
            section_df = df[df['Domain'] == domain_name].copy()
            if section_df.empty:
                st.info(f"No records for {domain_name}")
                return
            
            clean_df = get_clean_data(section_df)
            
            # Section Metrics
            s_total = clean_df['Amount'].sum()
            count = len(clean_df)
            
            m1, m2 = st.columns(2)
            m1.metric(f"Total {domain_name} Volume", f"₹{s_total:,.2f}")
            m2.metric("Total Entries", count)

            # Section Specific Plot
            st.write(f"**{domain_name} Spend Breakdown**")
            fig_sec = px.bar(clean_df, x='Sub-Category', y='Amount', color='Sub-Category', text_auto='.2s')
            st.plotly_chart(fig_sec, use_container_width=True)

            # Expander for Filters
            with st.expander("🔍 Advanced Filters"):
                # (Optional filters logic here)
                pass

            st.write("**Data Records**")
            st.dataframe(clean_df.sort_values('Date', ascending=False), use_container_width=True, hide_index=True)

    # --- RENDER OTHER TABS ---
    render_section_dashboard("Car", tabs[1])
    render_section_dashboard("Sheep", tabs[2])
    render_section_dashboard("Agri Land", tabs[3])
    render_section_dashboard("Home", tabs[4])
    render_section_dashboard("Personal", tabs[5])

    # Loans & EMI (Special handling for combined metrics)
    with tabs[6]:
        loan_df = df[df['Domain'].isin(["Loans", "EMI"])]
        if not loan_df.empty:
            clean_loan = get_clean_data(loan_df)
            st.metric("Total Debt/Liability", f"₹{clean_loan['Amount'].sum():,.2f}")
            fig_loan = px.area(clean_loan, x="Date", y="Amount", color="Domain")
            st.plotly_chart(fig_loan, use_container_width=True)
            st.dataframe(clean_loan, use_container_width=True)

    render_section_dashboard("Friends lending", tabs[7])
