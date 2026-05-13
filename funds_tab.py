import streamlit as st
import pandas as pd
import plotly.express as px
import json

def get_clean_data(df):
    if df.empty: return df
    extras = df['Extra Details'].apply(lambda x: json.loads(x) if pd.notnull(x) and x != "" else {})
    extras_df = pd.json_normalize(extras)
    extras_df.index = df.index
    return pd.concat([df.drop(columns=['Extra Details']), extras_df], axis=1)

def render_funds_tab(csv_file):
    try:
        df = pd.read_csv(csv_file)
        if not df.empty: df['Date'] = pd.to_datetime(df['Date']).dt.date
    except Exception:
        st.error("⚠️ Data file corrupted or missing.")
        return

    if df.empty:
        st.info("No financial records found. Head to the Data Entry form.")
        return

    # Dashboard Tabs
    tabs = st.tabs(["📊 Global Overview", "🚗 Car", "🐑 Sheep", "🌱 Agri Land", "🏠 Home", "🧍 Personal", "💸 Loans & EMI", "🤝 Friends Lending"])

    # --- TAB 0: GLOBAL BALANCE SHEET ---
    with tabs[0]:
        income = df[(df['Transaction Type'] == 'Received') & (df['Payment Status'].str.contains("Completed"))]['Amount'].sum()
        expense = df[(df['Transaction Type'] == 'Paid') & (df['Payment Status'].str.contains("Completed"))]['Amount'].sum()
        pending = df[df['Payment Status'].str.contains("Pending")]['Amount'].sum()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Realized Inflow", f"{income:,.2f}", delta="Income")
        col2.metric("Total Realized Outflow", f"{expense:,.2f}", delta="Expense", delta_color="inverse")
        col3.metric("Net Cash Flow", f"{(income - expense):,.2f}", delta="Balance")
        col4.metric("Total Pending/Expected", f"{pending:,.2f}", delta="Awaiting", delta_color="off")

        st.divider()

        c_chart1, c_chart2 = st.columns(2)
        with c_chart1:
            st.markdown("**Outflow Breakdown by Domain**")
            exp_df = df[df['Transaction Type'] == 'Paid']
            if not exp_df.empty:
                fig1 = px.pie(exp_df, values='Amount', names='Domain', hole=0.4, template="plotly_white")
                st.plotly_chart(fig1, use_container_width=True)
                
        with c_chart2:
            st.markdown("**Cashflow Timeline**")
            time_df = df.groupby(['Date', 'Transaction Type'])['Amount'].sum().reset_index()
            if not time_df.empty:
                fig2 = px.bar(time_df, x='Date', y='Amount', color='Transaction Type', barmode='group', template="plotly_white")
                st.plotly_chart(fig2, use_container_width=True)

        st.markdown("**Master Record Table**")
        st.dataframe(get_clean_data(df).sort_values('Date', ascending=False), use_container_width=True, hide_index=True)

    # --- DOMAIN SPECIFIC TABS GENERATOR ---
    def render_domain_dashboard(domain_name, tab_obj):
        with tab_obj:
            domain_df = df[df['Domain'] == domain_name].copy()
            if domain_df.empty:
                st.info(f"No data recorded for {domain_name} yet.")
                return

            clean_df = get_clean_data(domain_df)
            
            # Domain specific layout
            d_col1, d_col2 = st.columns([1, 2])
            
            with d_col1:
                total_vol = clean_df['Amount'].sum()
                st.metric(f"{domain_name} Total Volume", f"{total_vol:,.2f}")
                st.caption(f"Based on {len(clean_df)} total records.")

            with d_col2:
                # Dynamic Bar Chart based on Sub-Categories
                if 'Sub-Category' in clean_df.columns and not clean_df['Sub-Category'].isna().all():
                    fig = px.bar(clean_df, x='Sub-Category', y='Amount', color='Sub-Category', template="plotly_white", height=250)
                    fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=10, b=0))
                    st.plotly_chart(fig, use_container_width=True)

            # Dynamic Filter Expander
            with st.expander(f"🔍 Dynamic Filters for {domain_name}"):
                f_col1, f_col2 = st.columns(2)
                
                # Filter by Sub-Category if it exists
                if 'Sub-Category' in clean_df.columns:
                    subs = clean_df['Sub-Category'].dropna().unique().tolist()
                    selected_subs = f_col1.multiselect("Filter Sub-Category", subs, default=subs, key=f"sub_{domain_name}")
                    clean_df = clean_df[clean_df['Sub-Category'].isin(selected_subs)]
                
                # Filter by Bank Name
                if 'Bank Name' in clean_df.columns:
                    banks = clean_df['Bank Name'].dropna().unique().tolist()
                    selected_banks = f_col2.multiselect("Filter Bank Source", banks, default=banks, key=f"bank_{domain_name}")
                    clean_df = clean_df[clean_df['Bank Name'].isin(selected_banks)]

            # Fully Flattened Data Table showing by default
            st.dataframe(clean_df.sort_values('Date', ascending=False), use_container_width=True, hide_index=True)

    # Render Domains mapping to their respective tabs
    render_domain_dashboard("Car", tabs[1])
    render_domain_dashboard("Sheep", tabs[2])
    render_domain_dashboard("Agri Land", tabs[3])
    render_domain_dashboard("Home", tabs[4])
    render_domain_dashboard("Personal", tabs[5])
    
    # Combined Loans/EMI
    with tabs[6]:
        loan_df = df[df['Domain'].isin(["Loans", "EMI"])]
        if not loan_df.empty:
            clean_loan = get_clean_data(loan_df)
            st.metric("Total Outstanding / Assessed Principal", f"{clean_loan['Amount'].sum():,.2f}")
            st.dataframe(clean_loan.sort_values('Date', ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("No Loan or EMI records found.")

    render_domain_dashboard("Friends lending", tabs[7])
