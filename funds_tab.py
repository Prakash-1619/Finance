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
    default_cols = [c for c in ['Transaction Type', 'Person/Org Name', 'Sub-Category'] if c in df.columns]
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
    st.markdown(f"### 🗑️ Manage & Delete Records")
    if df_subset.empty:
        st.info("No records available.")
        return

    # Add search functionality for deletion
    search_query = st.text_input("🔍 Search record to delete (Description, Name, or Category):", key=f"search_del_{domain_name}")
    
    display_df = df_subset.copy()
    if search_query:
        # Search across multiple columns
        mask = display_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
        display_df = display_df[mask]

    if display_df.empty:
        st.warning("No records match your search.")
        return

    def format_record(idx):
        row = display_df.loc[idx]
        return f"[{row['Date']}] {row['Transaction Type']} - {row.get('Sub-Category', 'N/A')} - ₹{row['Amount']} ({row.get('Description', '')})"

    selected_index = st.selectbox("Select record to permanently remove:", options=display_df.index.tolist(), format_func=format_record, key=f"del_sel_{domain_name}")
    
    st.error(f"You are about to delete: {format_record(selected_index)}")
    confirm = st.checkbox("Confirm permanent deletion from GitHub", key=f"del_chk_{domain_name}")
    
    if st.button("🚨 Delete Record", type="primary", disabled=not confirm, key=f"del_btn_{domain_name}"):
        with st.spinner("Updating GitHub..."):
            full_df = load_data()
            full_df = full_df.drop(index=selected_index)
            success = save_data_to_github(full_df, commit_message=f"Deleted {domain_name} record")
            if success:
                st.success("✅ Record Deleted!")
                st.rerun()

def render_domain_dashboard(domain_name, tab_obj, global_df):
    with tab_obj:
        domain_df = global_df[global_df['Domain'] == domain_name].copy()
        if domain_df.empty:
            st.info(f"No records found for {domain_name}.")
            return

        clean_dom = get_clean_data(domain_df)
        filt_dom = apply_dynamic_filters(clean_dom, f"dom_{domain_name}")
        
        # UI Top N and Aggregation Control
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        with c1: top_n = st.number_input("Top N in Charts", 5, 20, 10, key=f"n_{domain_name}")
        with c2: freq = st.selectbox("Time Trend", ["Daily", "Weekly", "Monthly", "Quarterly"], key=f"f_{domain_name}")
        with c3: agg = st.selectbox("Metric", ["Sum", "Mean"], key=f"a_{domain_name}")
        
        # Sub-tabs as requested
        d_tabs = st.tabs(["📊 Balance Sheet", "🟥 Expenditure", "🟩 Income", "⚙️ Manage & Delete"])
        
        with d_tabs[0]: # Balance Sheet / Analytics
            inc_val = filt_dom[filt_dom['Transaction Type'].isin(['Income', 'Received'])]['Amount'].sum()
            exp_val = filt_dom[filt_dom['Transaction Type'].isin(['Expenditure', 'Paid'])]['Amount'].sum()
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Income", f"₹{inc_val:,.2f}")
            m2.metric("Total Exp.", f"₹{exp_val:,.2f}")
            m3.metric("Net Balance", f"₹{(inc_val - exp_val):,.2f}")

            # Time Series Line Chart
            ts_df = filt_dom.copy()
            ts_df['Date'] = pd.to_datetime(ts_df['Date'])
            freq_map = {"Daily": "D", "Weekly": "W", "Monthly": "ME", "Quarterly": "QE"}
            ts_res = ts_df.set_index('Date').groupby('Transaction Type').resample(freq_map[freq])['Amount'].agg(agg.lower()).reset_index()
            st.plotly_chart(px.line(ts_res, x='Date', y='Amount', color='Transaction Type', title=f"{freq} {agg} Trend"), use_container_width=True)

            # Pie & Bar split
            p_col1, p_col2 = st.columns(2)
            with p_col1:
                st.plotly_chart(px.pie(filt_dom, values='Amount', names='Sub-Category', title="Category Split"), use_container_width=True)
            with p_col2:
                pers_sum = filt_dom.groupby('Person/Org Name')['Amount'].sum().nlargest(top_n).reset_index()
                st.plotly_chart(px.bar(pers_sum, x='Person/Org Name', y='Amount', title=f"Top {top_n} Persons"), use_container_width=True)

        with d_tabs[1]: # Expenditure
            exp_df = filt_dom[filt_dom['Transaction Type'].isin(['Expenditure', 'Paid'])]
            st.dataframe(exp_df.sort_values('Date', ascending=False), use_container_width=True)

        with d_tabs[2]: # Income
            inc_df = filt_dom[filt_dom['Transaction Type'].isin(['Income', 'Received'])]
            st.dataframe(inc_df.sort_values('Date', ascending=False), use_container_width=True)

        with d_tabs[3]: # Manage & Delete
            render_delete_interface(domain_df, domain_name)

def render_funds_tab(data):
    df_raw = load_data()
    if df_raw.empty:
        st.info("No data found.")
        return

    df_raw['Date'] = pd.to_datetime(df_raw['Date']).dt.date
    
    st.markdown("### ⏱️ Global Time Filter")
    time_period = st.selectbox("Select Duration", ["All Time", "This Month", "Last 3 Months", "This Year", "Custom Range"])
    
    today = date.today()
    start_date, end_date = df_raw['Date'].min(), df_raw['Date'].max()
    if time_period == "This Month": start_date = today.replace(day=1)
    elif time_period == "This Year": start_date = today.replace(month=1, day=1)
    
    df = df_raw[(df_raw['Date'] >= start_date) & (df_raw['Date'] <= end_date)].copy()

    tabs = st.tabs(["📊 Overview", "🟩 Income", "🟥 Expenditure", "💸 Loans", "🚗 Car", "🐄 Cows", "🐑 Sheep", "🌱 Agri", "🏠 Home", "🧍 Personal", "🤝 Friends"])

    # Global Overview Logic
    with tabs[0]:
        master = get_clean_data(df)
        filt_g = apply_dynamic_filters(master, "global_main")
        st.dataframe(filt_g.sort_values('Date', ascending=False), use_container_width=True)

    # Domain Rendering
    dom_list = ["Car", "Cows", "Sheep", "Agri Land", "Home", "Personal", "Friends lending"]
    for i, d_name in enumerate(dom_list):
        render_domain_dashboard(d_name, tabs[i+4], df)
