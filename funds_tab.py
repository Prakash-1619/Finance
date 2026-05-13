import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import date, timedelta

# --- HELPER: Flatten JSON & Clean Data ---
def get_clean_data(df):
    if df.empty: return df
    extras = df['Extra Details'].apply(lambda x: json.loads(x) if pd.notnull(x) and x != "" else {})
    extras_df = pd.json_normalize(extras)
    extras_df.index = df.index 
    return pd.concat([df.drop(columns=['Extra Details']), extras_df], axis=1)

# --- HELPER: Advanced Filter Engine ---
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

# --- HELPER: Safe Delete Interface ---
def render_delete_interface(df_subset, csv_file, domain_name):
    st.markdown(f"### 🗑️ Delete Record")
    if df_subset.empty:
        st.info("No records available to delete.")
        return
        
    st.warning("⚠️ Warning: Deleting a record is permanent.")
    
    def format_record(idx):
        row = df_subset.loc[idx]
        return f"[{row['Date']}] {row['Transaction Type']} - {row.get('Sub-Category', 'N/A')} - ₹{row['Amount']}"

    selected_index = st.selectbox("Select record to delete:", options=df_subset.index.tolist(), format_func=format_record, key=f"del_sel_{domain_name}")
    confirm = st.checkbox("I confirm that I want to permanently delete this record.", key=f"del_chk_{domain_name}")
    
    if st.button("🚨 Delete Record", type="primary", disabled=not confirm, key=f"del_btn_{domain_name}"):
        full_df = pd.read_csv(csv_file)
        full_df = full_df.drop(index=selected_index)
        full_df.to_csv(csv_file, index=False)
        st.success("✅ Record deleted successfully!")
        st.rerun()

# --- MAIN RENDER FUNCTION ---
def render_funds_tab(csv_file):
    # ==========================================
    # FIX: Enhanced Error Catching
    # ==========================================
    try:
        df_raw = pd.read_csv(csv_file)
        if not df_raw.empty: df_raw['Date'] = pd.to_datetime(df_raw['Date']).dt.date
    except Exception as e:
        st.error(f"⚠️ Data file error: {e}")
        st.info("💡 Tip: If you recently added new columns to your form, you must delete 'data.csv' and let the app regenerate it.")
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

    # ==========================================
    # TOP LEVEL TABS
    # ==========================================
    tabs = st.tabs([
        "📊 Global Overview", "🟩 All Received", "🟥 All Paid", "💸 All Loans", 
        "🚗 Car", "🐑 Sheep", "🌱 Agri", "🏠 Home", "🧍 Personal", "🤝 Friends"
    ])

    # --- TAB 0: GLOBAL BALANCE SHEET ---
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
            st.markdown("**Income by Domain**")
            inc_df = filtered_global[filtered_global['Transaction Type'] == 'Received']
            if not inc_df.empty:
                st.plotly_chart(px.pie(inc_df, values='Amount', names='Domain', hole=0.4, template="plotly_white"), use_container_width=True)
            else: st.info("No income data.")
            
        with p_col2:
            st.markdown("**Expense by Domain**")
            exp_df = filtered_global[filtered_global['Transaction Type'] == 'Paid']
            if not exp_df.empty:
                st.plotly_chart(px.pie(exp_df, values='Amount', names='Domain', hole=0.4, template="plotly_white"), use_container_width=True)
            else: st.info("No expense data.")

        t_col1, t_col2 = st.columns(2)
        with t_col1:
            st.markdown("**Daily Cashflow Timeline**")
            time_df = filtered_global.groupby(['Date', 'Transaction Type'])['Amount'].sum().reset_index()
            if not time_df.empty:
                st.plotly_chart(px.bar(time_df, x='Date', y='Amount', color='Transaction Type', barmode='group', template="plotly_white"), use_container_width=True)
                
        with t_col2:
            st.markdown("**Cumulative Net Balance**")
            if not filtered_global.empty:
                bal_df = filtered_global.groupby(['Date', 'Transaction Type'])['Amount'].sum().unstack(fill_value=0).reset_index()
                if 'Received' not in bal_df: bal_df['Received'] = 0
                if 'Paid' not in bal_df: bal_df['Paid'] = 0
                bal_df['Daily Net'] = bal_df['Received'] - bal_df['Paid']
                bal_df['Cumulative'] = bal_df['Daily Net'].cumsum()
                st.plotly_chart(px.area(bal_df, x='Date', y='Cumulative', template="plotly_white"), use_container_width=True)

        st.markdown("**Filtered Master Data Table**")
        st.dataframe(filtered_global.sort_values('Date', ascending=False), use_container_width=True)

    # --- TAB 1: ALL RECEIVED ---
    with tabs[1]:
        rec_only = get_clean_data(df[df['Transaction Type'] == 'Received'])
        filt_rec = apply_dynamic_filters(rec_only, "all_rec")
        st.metric("Total Filtered Income", f"₹ {filt_rec['Amount'].sum():,.2f}")
        if not filt_rec.empty:
            st.plotly_chart(px.bar(filt_rec.groupby('Domain')['Amount'].sum().reset_index(), x='Domain', y='Amount', color='Domain', template="plotly_white"), use_container_width=True)
            st.dataframe(filt_rec.sort_values('Date', ascending=False), use_container_width=True)

    # --- TAB 2: ALL PAID ---
    with tabs[2]:
        paid_only = get_clean_data(df[df['Transaction Type'] == 'Paid'])
        filt_paid = apply_dynamic_filters(paid_only, "all_paid")
        st.metric("Total Filtered Expense", f"₹ {filt_paid['Amount'].sum():,.2f}")
        if not filt_paid.empty:
            st.plotly_chart(px.bar(filt_paid.groupby('Domain')['Amount'].sum().reset_index(), x='Domain', y='Amount', color='Domain', template="plotly_white"), use_container_width=True)
            st.dataframe(filt_paid.sort_values('Date', ascending=False), use_container_width=True)

    # --- TAB 3: ALL LOANS & EMI ---
    with tabs[3]:
        loan_df = df[df['Domain'].isin(["Loans", "EMI"])].copy()
        if not loan_df.empty:
            filt_loan = apply_dynamic_filters(get_clean_data(loan_df), "all_loans")
            st.metric("Total Filtered Liabilities", f"₹ {filt_loan['Amount'].sum():,.2f}")
            st.dataframe(filt_loan.sort_values('Date', ascending=False), use_container_width=True)
            render_delete_interface(loan_df, csv_file, "Loans/EMI")
        else: st.info("No Loans/EMI data.")

    # ==========================================
    # DOMAIN SPECIFIC DASHBOARDS (Tabs 4-9)
    # ==========================================
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
                
                if 'Sub-Category' in filt_dom.columns and not filt_dom.empty:
                    summary = filt_dom.groupby(['Sub-Category', 'Transaction Type'])['Amount'].sum().reset_index()
                    st.plotly_chart(px.bar(summary, x='Sub-Category', y='Amount', color='Transaction Type', barmode='group', template="plotly_white"), use_container_width=True)

            with sub_tabs[1]:
                s_paid = filt_dom[filt_dom['Transaction Type'] == 'Paid']
                if not s_paid.empty:
                    if 'Sub-Category' in s_paid.columns:
                        st.plotly_chart(px.pie(s_paid, values='Amount', names='Sub-Category', hole=0.5, template="plotly_white", height=300), use_container_width=True)
                    st.dataframe(s_paid.sort_values('Date', ascending=False), use_container_width=True)
                else: st.write("No paid records.")

            with sub_tabs[2]:
                s_rec = filt_dom[filt_dom['Transaction Type'] == 'Received']
                if not s_rec.empty:
                    if 'Sub-Category' in s_rec.columns:
                        st.plotly_chart(px.pie(s_rec, values='Amount', names='Sub-Category', hole=0.5, template="plotly_white", height=300), use_container_width=True)
                    st.dataframe(s_rec.sort_values('Date', ascending=False), use_container_width=True)
                else: st.write("No received records.")

            with sub_tabs[3]:
                render_delete_interface(domain_df, csv_file, domain_name)

    render_domain_dashboard("Car", tabs[4])
    render_domain_dashboard("Sheep", tabs[5])
    render_domain_dashboard("Agri Land", tabs[6])
    render_domain_dashboard("Home", tabs[7])
    render_domain_dashboard("Personal", tabs[8])
    render_domain_dashboard("Friends lending", tabs[9])
