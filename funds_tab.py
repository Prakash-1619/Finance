import streamlit as st
import pandas as pd
import plotly.express as px
import json
from datetime import date, timedelta
from github_sync import load_data, save_data_to_github

def get_clean_data(df):
    if df.empty: return df
    # Safely parse JSON from the Extra Details column
    extras = df['Extra Details'].apply(lambda x: json.loads(x) if pd.notnull(x) and x != "" else {})
    extras_df = pd.json_normalize(extras)
    extras_df.index = df.index 
    return pd.concat([df.drop(columns=['Extra Details']), extras_df], axis=1)

def apply_dynamic_filters(df, prefix_key):
    if df.empty: return df
    st.markdown(f"###### 🔎 Dynamic Filters")
    
    # Priority filters: Person/Org and Transaction Type
    default_cols = [c for c in ['Transaction Type', 'Person/Org Name', 'Domain', 'Sub-Category'] if c in df.columns]
    filter_cols = st.multiselect("Select columns to filter by:", df.columns.tolist(), default=default_cols, key=f"sel_{prefix_key}")
    
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
            full_df = load_data()
            full_df = full_df.drop(index=selected_index)
            success = save_data_to_github(full_df, commit_message=f"Deleted record from {domain_name}")
            if success:
                st.success("✅ Record successfully deleted from GitHub!")
                st.rerun()

def render_funds_tab(data):
    # Pull fresh data from GitHub
    df_raw = load_data()

    if df_raw.empty:
        st.info("No financial records found. Head to the Data Entry form.")
        return
        
    df_raw['Date'] = pd.to_datetime(df_raw['Date']).dt.date
    # Prepare monthly/daily labels for plotting
    df_raw['Month'] = pd.to_datetime(df_raw['Date']).dt.strftime('%Y-%m')

    st.markdown("### ⏱️ Global Time Filter")
    time_col1, time_col2 = st.columns([1, 2])
    with time_col1:
        time_period = st.selectbox("Select Duration", ["All Time", "This Month", "Last Month", "Last 3 Months", "Last 6 Months", "This Year", "Custom Range"])
    
    today = date.today()
    start_date, end_date = df_raw['Date'].min(), df_raw['Date'].max()

    if time_period == "This Month": start_date = today.replace(day=1)
    elif time_period == "Last Month": start_date, end_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1), today.replace(day=1) - timedelta(days=1)
    elif time_period == "Last 3 Months": start_date = today - timedelta(days=90)
    elif time_period == "This Year": start_date = today.replace(month=1, day=1)
    elif time_period == "Custom Range":
        with time_col2:
            dates = st.date_input("Select Date Range", [start_date, end_date])
            if len(dates) == 2: start_date, end_date = dates

    df = df_raw[(df_raw['Date'] >= start_date) & (df_raw['Date'] <= end_date)].copy()
    st.divider()

    # Updated Tabs to include 'Cows'
    tabs = st.tabs(["📊 Global Overview", "🟩 Received", "🟥 Paid", "💸 Loans", "🚗 Car", "🐄 Cows", "🐑 Sheep", "🌱 Agri", "🏠 Home", "🧍 Personal", "🤝 Friends"])

    # TAB 0: GLOBAL BALANCE SHEET
    with tabs[0]:
        clean_master = get_clean_data(df)
        filtered_global = apply_dynamic_filters(clean_master, "global")
        
        income = filtered_global[filtered_global['Transaction Type'].isin(['Received', 'Income'])]['Amount'].sum()
        expense = filtered_global[filtered_global['Transaction Type'].isin(['Paid', 'Expenditure'])]['Amount'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Inflow", f"₹ {income:,.2f}")
        c2.metric("Total Outflow", f"₹ {expense:,.2f}")
        c3.metric("Net Balance", f"₹ {(income - expense):,.2f}")
        st.divider()
        
        # New Plots: Person & Category Wise
        st.markdown("#### 📈 In-depth Analytics")
        g_col1, g_col2 = st.columns(2)
        with g_col1:
            st.plotly_chart(px.bar(filtered_global, x='Month', y='Amount', color='Transaction Type', barmode='group', title="Monthly Trend"), use_container_width=True)
        with g_col2:
            st.plotly_chart(px.bar(filtered_global, x='Person/Org Name', y='Amount', color='Domain', title="Expenditure/Income by Person"), use_container_width=True)

        st.dataframe(filtered_global.sort_values('Date', ascending=False), use_container_width=True)

    # Individual Transaction Type Tabs
    with tabs[1]: # Received
        filt_rec = apply_dynamic_filters(get_clean_data(df[df['Transaction Type'].isin(['Received', 'Income'])]), "all_rec")
        st.metric("Total Received", f"₹ {filt_rec['Amount'].sum():,.2f}")
        st.plotly_chart(px.bar(filt_rec, x='Date', y='Amount', color='Person/Org Name', title="Daily Inflow by Source"), use_container_width=True)
        st.dataframe(filt_rec.sort_values('Date', ascending=False), use_container_width=True)

    with tabs[2]: # Paid
        filt_paid = apply_dynamic_filters(get_clean_data(df[df['Transaction Type'].isin(['Paid', 'Expenditure'])]), "all_paid")
        st.metric("Total Paid", f"₹ {filt_paid['Amount'].sum():,.2f}")
        st.plotly_chart(px.pie(filt_paid, values='Amount', names='Domain', title="Expense Distribution by Domain"), use_container_width=True)
        st.dataframe(filt_paid.sort_values('Date', ascending=False), use_container_width=True)

    with tabs[3]: # Loans
        loan_df = df[df['Domain'].isin(["Loans", "EMI"])].copy()
        if not loan_df.empty:
            filt_loan = apply_dynamic_filters(get_clean_data(loan_df), "all_loans")
            st.metric("Total Liabilities", f"₹ {filt_loan['Amount'].sum():,.2f}")
            st.dataframe(filt_loan.sort_values('Date', ascending=False), use_container_width=True)
            render_delete_interface(loan_df, "Loans/EMI")

    # Domain Dashboard Helper
    def render_domain_dashboard(domain_name, tab_obj):
        with tab_obj:
            domain_df = df[df['Domain'] == domain_name].copy()
            if domain_df.empty:
                st.info(f"No records for {domain_name}.")
                return

            clean_dom = get_clean_data(domain_df)
            filt_dom = apply_dynamic_filters(clean_dom, f"dom_{domain_name}")
            
            d_subtabs = st.tabs(["📊 Analytics", "📄 Data Table", "⚙️ Manage"])
            
            with d_subtabs[0]:
                m1, m2 = st.columns(2)
                d_in = filt_dom[filt_dom['Transaction Type'].isin(['Received', 'Income'])]['Amount'].sum()
                d_out = filt_dom[filt_dom['Transaction Type'].isin(['Paid', 'Expenditure'])]['Amount'].sum()
                m1.metric("Domain Inflow", f"₹ {d_in:,.2f}")
                m2.metric("Domain Outflow", f"₹ {d_out:,.2f}")
                
                # Person & Category Plots
                p1, p2 = st.columns(2)
                with p1:
                    st.plotly_chart(px.pie(filt_dom, values='Amount', names='Sub-Category', title="Split by Sub-Category"), use_container_width=True)
                with p2:
                    st.plotly_chart(px.bar(filt_dom, x='Person/Org Name', y='Amount', color='Transaction Type', title="Activity by Person"), use_container_width=True)
                
                st.plotly_chart(px.line(filt_dom.sort_values('Date'), x='Date', y='Amount', markers=True, title="Timeline of Transactions"), use_container_width=True)

            with d_subtabs[1]:
                st.dataframe(filt_dom.sort_values('Date', ascending=False), use_container_width=True)

            with d_subtabs[2]:
                render_delete_interface(domain_df, domain_name)

    # Rendering all Domain Tabs
    render_domain_dashboard("Car", tabs[4])
    render_domain_dashboard("Cows", tabs[5]) # Added Cows
    render_domain_dashboard("Sheep", tabs[6])
    render_domain_dashboard("Agri Land", tabs[7])
    render_domain_dashboard("Home", tabs[8])
    render_domain_dashboard("Personal", tabs[9])
    render_domain_dashboard("Friends lending", tabs[10])
