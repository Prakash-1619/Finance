import streamlit as st
import pandas as pd
import plotly.express as px
import json
from datetime import date, timedelta
from github_sync import load_data, save_data_to_github

def get_clean_data(df):
    if df.empty: return df
    extras = df['Extra Details'].apply(lambda x: json.loads(x) if pd.notnull(x) and x != "" else {})
    extras_df = pd.json_normalize(extras)
    extras_df.index = df.index 
    return pd.concat([df.drop(columns=['Extra Details']), extras_df], axis=1)

def apply_dynamic_filters(df, prefix_key):
    if df.empty: return df
    st.markdown(f"###### 🔎 Dynamic Filters")
    filter_cols = st.multiselect("Select columns to filter by:", df.columns.tolist(), key=f"sel_{prefix_key}")
    filtered_df = df.copy()
    if filter_cols:
        cols = st.columns(min(len(filter_cols), 4))
        for i, col in enumerate(filter_cols):
            with cols[i % 4]:
                unique_vals = filtered_df[col].dropna().unique().tolist()
                selected_vals = st.multiselect(f"{col}", unique_vals, default=unique_vals, key=f"val_{prefix_key}_{col}")
                filtered_df = filtered_df[filtered_df[col].isin(selected_vals)]
    return filtered_df

def render_delete_interface(df_subset, domain_name):
    st.markdown(f"### 🗑️ Delete Record from GitHub")
    if df_subset.empty:
        st.info("No records available to delete.")
        return
        
    st.warning("⚠️ Warning: This will permanently remove the record from your GitHub repository.")
    
    def format_record(idx):
        row = df_subset.loc[idx]
        return f"[{row['Date']}] {row['Transaction Type']} - {row.get('Sub-Category', 'N/A')} - ₹{row['Amount']}"

    selected_index = st.selectbox("Select record to delete:", options=df_subset.index.tolist(), format_func=format_record, key=f"del_sel_{domain_name}")
    confirm = st.checkbox("I confirm that I want to permanently delete this record.", key=f"del_chk_{domain_name}")
    
    if st.button("🚨 Delete Record", type="primary", disabled=not confirm, key=f"del_btn_{domain_name}"):
        with st.spinner("Deleting from GitHub..."):
            # 1. Pull fresh data to ensure accurate row indices
            full_df = load_data()
            
            # 2. Drop the row
            full_df = full_df.drop(index=selected_index)
            
            # 3. Commit the change
            success = save_data_to_github(full_df, commit_message=f"Deleted record from {domain_name}")
            
            if success:
                st.success("✅ Record successfully deleted from GitHub!")
                st.rerun()

def render_funds_tab(data): # It's expecting 'data' here
    # Load directly from GitHub
    df_raw = load_data()

    if df_raw.empty:
        st.info("No financial records found or waiting for connection. Head to the Data Entry form.")
        return
        
    # Convert dates
    df_raw['Date'] = pd.to_datetime(df_raw['Date']).dt.date

    # --- TIME FILTER ---
    st.markdown("### ⏱️ Global Time Filter")
    time_col1, time_col2 = st.columns([1, 2])
    with time_col1:
        time_period = st.selectbox("Select Duration", ["All Time", "This Month", "Last Month", "Last 3 Months", "Last 6 Months", "This Year", "Custom Range"])
    
    today = date.today()
    start_date, end_date = df_raw['Date'].min(), df_raw['Date'].max()

    if time_period == "This Month": start_date = today.replace(day=1)
    elif time_period == "Last Month": start_date, end_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1), today.replace(day=1) - timedelta(days=1)
    elif time_period == "Last 3 Months": start_date = today - timedelta(days=90)
    elif time_period == "Last 6 Months": start_date = today - timedelta(days=180)
    elif time_period == "This Year": start_date = today.replace(month=1, day=1)
    elif time_period == "Custom Range":
        with time_col2:
            dates = st.date_input("Select Date Range", [start_date, end_date])
            if len(dates) == 2: start_date, end_date = dates

    df = df_raw[(df_raw['Date'] >= start_date) & (df_raw['Date'] <= end_date)].copy()
    st.divider()

    tabs = st.tabs(["📊 Global Overview", "🟩 All Received", "🟥 All Paid", "💸 All Loans", "🚗 Car", "🐑 Sheep", "🌱 Agri", "🏠 Home", "🧍 Personal", "🤝 Friends"])

    # TAB 0: GLOBAL BALANCE SHEET
    with tabs[0]:
        clean_master = get_clean_data(df)
        filtered_global = apply_dynamic_filters(clean_master, "global")
        
        income = filtered_global[filtered_global['Transaction Type'] == 'Received']['Amount'].sum()
        expense = filtered_global[filtered_global['Transaction Type'] == 'Paid']['Amount'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Inflow", f"₹ {income:,.2f}", delta="Income")
        c2.metric("Total Outflow", f"₹ {expense:,.2f}", delta="Expense", delta_color="inverse")
        c3.metric("Net Balance", f"₹ {(income - expense):,.2f}", delta="Profit/Loss")
        st.divider()
        
        p_col1, p_col2 = st.columns(2)
        with p_col1:
            inc_df = filtered_global[filtered_global['Transaction Type'] == 'Received']
            if not inc_df.empty: st.plotly_chart(px.pie(inc_df, values='Amount', names='Domain', hole=0.4, title="Income", template="plotly_white"), use_container_width=True)
            
        with p_col2:
            exp_df = filtered_global[filtered_global['Transaction Type'] == 'Paid']
            if not exp_df.empty: st.plotly_chart(px.pie(exp_df, values='Amount', names='Domain', hole=0.4, title="Expense", template="plotly_white"), use_container_width=True)

        t_col1, t_col2 = st.columns(2)
        with t_col1:
            time_df = filtered_global.groupby(['Date', 'Transaction Type'])['Amount'].sum().reset_index()
            if not time_df.empty: st.plotly_chart(px.bar(time_df, x='Date', y='Amount', color='Transaction Type', barmode='group', title="Timeline", template="plotly_white"), use_container_width=True)
                
        with t_col2:
            if not filtered_global.empty:
                bal_df = filtered_global.groupby(['Date', 'Transaction Type'])['Amount'].sum().unstack(fill_value=0).reset_index()
                if 'Received' not in bal_df: bal_df['Received'] = 0
                if 'Paid' not in bal_df: bal_df['Paid'] = 0
                bal_df['Daily Net'] = bal_df['Received'] - bal_df['Paid']
                bal_df['Cumulative'] = bal_df['Daily Net'].cumsum()
                st.plotly_chart(px.area(bal_df, x='Date', y='Cumulative', title="Cumulative", template="plotly_white"), use_container_width=True)

        st.dataframe(filtered_global.sort_values('Date', ascending=False), use_container_width=True)

    with tabs[1]:
        filt_rec = apply_dynamic_filters(get_clean_data(df[df['Transaction Type'] == 'Received']), "all_rec")
        st.metric("Filtered Income", f"₹ {filt_rec['Amount'].sum():,.2f}")
        if not filt_rec.empty: st.dataframe(filt_rec.sort_values('Date', ascending=False), use_container_width=True)

    with tabs[2]:
        filt_paid = apply_dynamic_filters(get_clean_data(df[df['Transaction Type'] == 'Paid']), "all_paid")
        st.metric("Filtered Expense", f"₹ {filt_paid['Amount'].sum():,.2f}")
        if not filt_paid.empty: st.dataframe(filt_paid.sort_values('Date', ascending=False), use_container_width=True)

    with tabs[3]:
        loan_df = df[df['Domain'].isin(["Loans", "EMI"])].copy()
        if not loan_df.empty:
            filt_loan = apply_dynamic_filters(get_clean_data(loan_df), "all_loans")
            st.metric("Total Liabilities", f"₹ {filt_loan['Amount'].sum():,.2f}")
            st.dataframe(filt_loan.sort_values('Date', ascending=False), use_container_width=True)
            render_delete_interface(loan_df, "Loans/EMI")

    def render_domain_dashboard(domain_name, tab_obj):
        with tab_obj:
            domain_df = df[df['Domain'] == domain_name].copy()
            if domain_df.empty:
                st.info(f"No records for {domain_name}.")
                return

            clean_dom = get_clean_data(domain_df)
            filt_dom = apply_dynamic_filters(clean_dom, f"dom_{domain_name}")
            sub_tabs = st.tabs(["📊 Section Balance", "🟥 Paid (Expense)", "🟩 Received (Income)", "⚙️ Manage & Delete"])
            
            with sub_tabs[0]:
                d_in = filt_dom[filt_dom['Transaction Type'] == 'Received']['Amount'].sum()
                d_out = filt_dom[filt_dom['Transaction Type'] == 'Paid']['Amount'].sum()
                m1, m2, m3 = st.columns(3)
                m1.metric("Inflow", f"₹ {d_in:,.2f}")
                m2.metric("Outflow", f"₹ {d_out:,.2f}")
                m3.metric("Net", f"₹ {(d_in - d_out):,.2f}")
                
            with sub_tabs[1]:
                s_paid = filt_dom[filt_dom['Transaction Type'] == 'Paid']
                if not s_paid.empty: st.dataframe(s_paid.sort_values('Date', ascending=False), use_container_width=True)

            with sub_tabs[2]:
                s_rec = filt_dom[filt_dom['Transaction Type'] == 'Received']
                if not s_rec.empty: st.dataframe(s_rec.sort_values('Date', ascending=False), use_container_width=True)

            with sub_tabs[3]:
                # Pass the domain data to the new Github Delete interface
                render_delete_interface(domain_df, domain_name)

    render_domain_dashboard("Car", tabs[4])
    render_domain_dashboard("Sheep", tabs[5])
    render_domain_dashboard("Agri Land", tabs[6])
    render_domain_dashboard("Home", tabs[7])
    render_domain_dashboard("Personal", tabs[8])
    render_domain_dashboard("Friends lending", tabs[9])
