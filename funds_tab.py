import streamlit as st
import pandas as pd
import plotly.express as px
import json
from datetime import date, timedelta

# --- HELPER: Flatten JSON & Clean Data ---
def get_clean_data(df):
    if df.empty: return df
    extras = df['Extra Details'].apply(lambda x: json.loads(x) if pd.notnull(x) and x != "" else {})
    extras_df = pd.json_normalize(extras)
    # Ensure indices align perfectly for deletion and joining
    extras_df.index = df.index 
    return pd.concat([df.drop(columns=['Extra Details']), extras_df], axis=1)

# --- HELPER: Advanced Column Filters ---
def render_dynamic_filters(df, prefix_key):
    if df.empty: return df
    st.markdown("###### 🔎 Dynamic Filters")
    
    # Let user pick which columns they want to filter by
    filter_cols = st.multiselect("Select columns to filter by:", df.columns.tolist(), key=f"sel_cols_{prefix_key}")
    
    filtered_df = df.copy()
    if filter_cols:
        cols = st.columns(min(len(filter_cols), 4)) # Max 4 columns wide
        for i, col in enumerate(filter_cols):
            with cols[i % 4]:
                unique_vals = filtered_df[col].dropna().unique().tolist()
                selected_vals = st.multiselect(f"Filter {col}", unique_vals, default=unique_vals, key=f"val_{prefix_key}_{col}")
                filtered_df = filtered_df[filtered_df[col].isin(selected_vals)]
    return filtered_df

# --- HELPER: Safe Delete Interface ---
def render_delete_interface(df_subset, csv_file, domain_name):
    st.markdown(f"### 🗑️ Delete {domain_name} Record")
    if df_subset.empty:
        st.info("No records available to delete.")
        return
        
    st.warning("⚠️ Warning: Deleting a record is permanent and will update your balance sheet instantly.")
    
    # Format options for the dropdown so the user knows exactly what they are deleting
    def format_record(idx):
        row = df_subset.loc[idx]
        return f"[{row['Date']}] {row['Transaction Type']} - {row['Sub-Category']} - ₹{row['Amount']}"

    selected_index = st.selectbox(
        "Select the exact record to delete:", 
        options=df_subset.index.tolist(), 
        format_func=format_record,
        key=f"del_sel_{domain_name}"
    )

    # Confirmation Logic
    confirm = st.checkbox("I confirm that I want to permanently delete this record.", key=f"del_chk_{domain_name}")
    
    if st.button("🚨 Delete Record", type="primary", disabled=not confirm, key=f"del_btn_{domain_name}"):
        # Load fresh original data to avoid index mismatch
        full_df = pd.read_csv(csv_file)
        full_df = full_df.drop(index=selected_index)
        full_df.to_csv(csv_file, index=False)
        st.success("✅ Record deleted successfully!")
        st.rerun()

# --- MAIN RENDER FUNCTION ---
def render_funds_tab(csv_file):
    try:
        # Load data, keeping original indices intact for exact row deletion
        df_raw = pd.read_csv(csv_file)
        if not df_raw.empty: 
            df_raw['Date'] = pd.to_datetime(df_raw['Date']).dt.date
    except Exception:
        st.error("⚠️ Data file corrupted or missing.")
        return

    if df_raw.empty:
        st.info("No financial records found. Head to the Data Entry form.")
        return

    # ==========================================
    # GLOBAL TIME FILTER
    # ==========================================
    st.markdown("### ⏱️ Global Time Filter")
    time_col1, time_col2 = st.columns([1, 2])
    
    with time_col1:
        time_period = st.selectbox("Select Duration", [
            "All Time", "This Month", "Last Month", "Last 3 Months", 
            "Last 6 Months", "This Year", "Custom Range"
        ])
    
    today = date.today()
    start_date, end_date = df_raw['Date'].min(), df_raw['Date'].max()

    if time_period == "This Month":
        start_date = today.replace(day=1)
    elif time_period == "Last Month":
        first_of_this_month = today.replace(day=1)
        end_date = first_of_this_month - timedelta(days=1)
        start_date = end_date.replace(day=1)
    elif time_period == "Last 3 Months":
        start_date = today - timedelta(days=90)
    elif time_period == "Last 6 Months":
        start_date = today - timedelta(days=180)
    elif time_period == "This Year":
        start_date = today.replace(month=1, day=1)
    elif time_period == "Custom Range":
        with time_col2:
            dates = st.date_input("Select Date Range", [start_date, end_date])
            if len(dates) == 2:
                start_date, end_date = dates

    # Apply Time Filter globally
    df = df_raw[(df_raw['Date'] >= start_date) & (df_raw['Date'] <= end_date)].copy()
    
    st.divider()

    # Dashboard Tabs
    tabs = st.tabs(["📊 Global Overview", "🚗 Car", "🐑 Sheep", "🌱 Agri Land", "🏠 Home", "🧍 Personal", "💸 Loans & EMI", "🤝 Friends Lending"])

    # ==========================================
    # TAB 0: GLOBAL BALANCE SHEET
    # ==========================================
    with tabs[0]:
        income = df[(df['Transaction Type'] == 'Received')]['Amount'].sum()
        expense = df[(df['Transaction Type'] == 'Paid')]['Amount'].sum()
        balance = income - expense

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Inflow (All Domains)", f"₹ {income:,.2f}", delta="Income")
        col2.metric("Total Outflow (All Domains)", f"₹ {expense:,.2f}", delta="Expense", delta_color="inverse")
        col3.metric("Overall Net Balance", f"₹ {balance:,.2f}", delta="Profit/Loss")

        st.markdown("**Master Filterable Data Table**")
        clean_master = get_clean_data(df)
        filtered_master = render_dynamic_filters(clean_master, "global")
        st.dataframe(filtered_master.sort_values('Date', ascending=False), use_container_width=True)

    # ==========================================
    # DOMAIN SPECIFIC DASHBOARDS GENERATOR
    # ==========================================
    def render_domain_dashboard(domain_name, tab_obj):
        with tab_obj:
            domain_df = df[df['Domain'] == domain_name].copy()
            if domain_df.empty:
                st.info(f"No data recorded for {domain_name} in this timeframe.")
                return

            clean_df = get_clean_data(domain_df)
            
            # SUB-TABS within the Domain
            sub_tabs = st.tabs(["📊 Section Balance", "🟥 Paid (Expense)", "🟩 Received (Income)", "⚙️ Manage & Delete"])
            
            # Sub-Tab 1: Balance Sheet
            with sub_tabs[0]:
                d_in = clean_df[clean_df['Transaction Type'] == 'Received']['Amount'].sum()
                d_out = clean_df[clean_df['Transaction Type'] == 'Paid']['Amount'].sum()
                
                m1, m2, m3 = st.columns(3)
                m1.metric(f"{domain_name} Inflow", f"₹ {d_in:,.2f}")
                m2.metric(f"{domain_name} Outflow", f"₹ {d_out:,.2f}")
                m3.metric(f"{domain_name} Net", f"₹ {(d_in - d_out):,.2f}")
                
                if 'Sub-Category' in clean_df.columns:
                    st.markdown(f"**{domain_name} Summary by Category**")
                    summary = clean_df.groupby(['Sub-Category', 'Transaction Type'])['Amount'].sum().reset_index()
                    fig = px.bar(summary, x='Sub-Category', y='Amount', color='Transaction Type', barmode='group')
                    st.plotly_chart(fig, use_container_width=True)

            # Sub-Tab 2: Paid (Expenses)
            with sub_tabs[1]:
                paid_df = clean_df[clean_df['Transaction Type'] == 'Paid']
                if not paid_df.empty:
                    f_paid = render_dynamic_filters(paid_df, f"{domain_name}_paid")
                    st.dataframe(f_paid.sort_values('Date', ascending=False), use_container_width=True)
                else:
                    st.write("No paid transactions.")

            # Sub-Tab 3: Received (Income)
            with sub_tabs[2]:
                rec_df = clean_df[clean_df['Transaction Type'] == 'Received']
                if not rec_df.empty:
                    f_rec = render_dynamic_filters(rec_df, f"{domain_name}_rec")
                    st.dataframe(f_rec.sort_values('Date', ascending=False), use_container_width=True)
                else:
                    st.write("No received transactions.")

            # Sub-Tab 4: Manage & Delete
            with sub_tabs[3]:
                render_delete_interface(domain_df, csv_file, domain_name)

    # Render Domains
    render_domain_dashboard("Car", tabs[1])
    render_domain_dashboard("Sheep", tabs[2])
    render_domain_dashboard("Agri Land", tabs[3])
    render_domain_dashboard("Home", tabs[4])
    render_domain_dashboard("Personal", tabs[5])
    
    # Combined Loans/EMI Custom Handling
    with tabs[6]:
        loan_df = df[df['Domain'].isin(["Loans", "EMI"])].copy()
        if not loan_df.empty:
            clean_loan = get_clean_data(loan_df)
            l_tabs = st.tabs(["📊 Overview", "⚙️ Manage & Delete"])
            
            with l_tabs[0]:
                st.metric("Total Liabilities Tracked", f"₹ {clean_loan['Amount'].sum():,.2f}")
                filtered_loan = render_dynamic_filters(clean_loan, "loans")
                st.dataframe(filtered_loan.sort_values('Date', ascending=False), use_container_width=True)
                
            with l_tabs[1]:
                render_delete_interface(loan_df, csv_file, "Loans & EMI")
        else:
            st.info("No Loan or EMI records found.")

    render_domain_dashboard("Friends lending", tabs[7])
