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
    default_cols = [c for c in ['Transaction Type', 'Domain', 'Person/Org Name', 'Sub-Category', 'Bank Name', 'Payment App'] if c in df.columns]
    filter_cols = st.multiselect("Select columns to filter by:", df.columns.tolist(), default=default_cols[:3], key=f"sel_{prefix_key}")
    filtered_df = df.copy()
    if filter_cols:
        cols = st.columns(min(len(filter_cols), 4))
        for i, col in enumerate(filter_cols):
            with cols[i % 4]:
                unique_vals = filtered_df[col].dropna().unique().tolist()
                selected_vals = st.multiselect(f"{col}", unique_vals, default=unique_vals, key=f"val_{prefix_key}_{col}")
                filtered_df = filtered_df[filtered_df[col].isin(selected_vals)]
    return filtered_df

def render_flexible_plots(df, key_prefix):
    """Allows user to choose which columns to visualize as plots."""
    if df.empty: return
    
    st.markdown("#### 📊 Custom Visualizations")
    plot_options = ['Domain', 'Sub-Category', 'Person/Org Name', 'Bank Name', 'Payment App', 'Org Name']
    available_options = [opt for opt in plot_options if opt in df.columns]
    
    selected_plots = st.multiselect(
        "Choose columns to show as charts:", 
        available_options, 
        default=available_options[:2], 
        key=f"plot_sel_{key_prefix}"
    )
    
    if selected_plots:
        for i in range(0, len(selected_plots), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(selected_plots):
                    col_name = selected_plots[i+j]
                    with cols[j]:
                        fig_data = df.groupby(col_name)['Amount'].sum().reset_index()
                        fig = px.pie(fig_data, values='Amount', names=col_name, title=f"Total by {col_name}", hole=0.4)
                        st.plotly_chart(fig, use_container_width=True, key=f"pie_{key_prefix}_{col_name}")

def render_delete_interface(df_subset, domain_name):
    st.markdown(f"### 🗑️ Manage & Delete Records")
    if df_subset.empty:
        st.info("No records available.")
        return

    search_query = st.text_input("🔍 Search record to delete:", key=f"search_del_{domain_name}")
    display_df = df_subset.copy()
    if search_query:
        mask = display_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
        display_df = display_df[mask]

    if display_df.empty:
        st.warning("No records match.")
        return

    def format_record(idx):
        row = display_df.loc[idx]
        return f"[{row['Date']}] {row['Transaction Type']} - {row.get('Sub-Category', 'N/A')} - ₹{row['Amount']}"

    selected_index = st.selectbox("Select record:", options=display_df.index.tolist(), format_func=format_record, key=f"del_sel_{domain_name}")
    confirm = st.checkbox("Confirm deletion", key=f"del_chk_{domain_name}")
    
    if st.button("🚨 Delete", type="primary", disabled=not confirm, key=f"del_btn_{domain_name}"):
        full_df = load_data()
        full_df = full_df.drop(index=selected_index)
        if save_data_to_github(full_df, commit_message=f"Deleted {domain_name} record"):
            st.success("Deleted!")
            st.rerun()

def render_domain_dashboard(domain_name, tab_obj, df_raw, start_date, end_date):
    with tab_obj:
        # 1. Get ALL TIME data for this domain
        domain_df_all = df_raw[df_raw['Domain'] == domain_name].copy()
        if domain_df_all.empty:
            st.info(f"No records for {domain_name}.")
            return

        # 2. Clean and apply Dynamic Filters to the ALL TIME data
        clean_dom_all = get_clean_data(domain_df_all)
        filt_dom_all = apply_dynamic_filters(clean_dom_all, f"dom_{domain_name}")
        
        # 3. Create the Time-Filtered slice for the regular metrics & tables
        mask_time = (filt_dom_all['Date'] >= start_date) & (filt_dom_all['Date'] <= end_date)
        filt_dom = filt_dom_all[mask_time]
        
        d_tabs = st.tabs(["📊 Balance Sheet", "🟥 Expenditure", "🟩 Income", "⚙️ Manage & Delete"])
        
        with d_tabs[0]: # Balance Sheet
            inc_val = filt_dom[filt_dom['Transaction Type'].isin(['Income', 'Received'])]['Amount'].sum()
            exp_val = filt_dom[filt_dom['Transaction Type'].isin(['Expenditure', 'Paid'])]['Amount'].sum()
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Income (Period)", f"₹{inc_val:,.2f}")
            m2.metric("Total Exp. (Period)", f"₹{exp_val:,.2f}")
            m3.metric("Net Balance (Period)", f"₹{(inc_val - exp_val):,.2f}")
            
            c1, c2 = st.columns(2)
            with c1: freq = st.selectbox("Frequency", ["Daily", "Weekly", "Monthly", "Quarterly"], key=f"f_{domain_name}")
            with c2: agg = st.selectbox("Metric", ["Sum", "Mean"], key=f"a_{domain_name}")
            
            # Sub-domain Periodic Trend
            ts_df = filt_dom.copy()
            ts_df['Date'] = pd.to_datetime(ts_df['Date'])
            freq_map = {"Daily": "D", "Weekly": "W", "Monthly": "ME", "Quarterly": "QE"}
            ts_res = ts_df.set_index('Date').groupby('Transaction Type').resample(freq_map[freq])['Amount'].agg(agg.lower()).reset_index()
            
            fig_ts = px.line(ts_res, x='Date', y='Amount', color='Transaction Type', markers=True, title=f"{freq} Trend (Selected Period)")
            st.plotly_chart(fig_ts, use_container_width=True, key=f"line_bal_{domain_name}")

            render_flexible_plots(filt_dom, f"bal_{domain_name}")

            # --- CUMULATIVE NET BALANCE (ALL TIME SMOOTHED AREA) ---
            ts_dom_all = filt_dom_all.copy()
            ts_dom_all['Date'] = pd.to_datetime(ts_dom_all['Date'])
            ts_res_all = ts_dom_all.set_index('Date').groupby('Transaction Type').resample(freq_map[freq])['Amount'].agg(agg.lower()).reset_index()

            if not ts_res_all.empty:
                st.markdown("#### 📉 Cumulative Net Balance (All-Time Net Flow)")
                net_df_d = ts_res_all.copy()
                net_df_d['Type'] = net_df_d['Transaction Type'].replace({'Received': 'Income', 'Paid': 'Expenditure'})
                net_pivot_d = net_df_d.pivot_table(index='Date', columns='Type', values='Amount', aggfunc='sum').fillna(0)
                for col in ['Income', 'Expenditure']:
                    if col not in net_pivot_d.columns:
                        net_pivot_d[col] = 0
                
                # Calculate Running Cumulative Sum
                net_pivot_d['Net Balance'] = net_pivot_d['Income'] - net_pivot_d['Expenditure']
                net_pivot_d['Cumulative Net'] = net_pivot_d['Net Balance'].cumsum()
                net_pivot_d = net_pivot_d.reset_index()
                
                # Determine color based on current (latest) net value
                current_net_d = net_pivot_d['Cumulative Net'].iloc[-1] if not net_pivot_d.empty else 0
                if current_net_d < 0:
                    area_color_d = '#EF553B' # Red
                elif current_net_d < 5000:
                    area_color_d = '#636EFA' # Blue
                else:
                    area_color_d = '#00CC96' # Green

                # Smoothed Area Plot
                fig_net_d = px.area(net_pivot_d, x='Date', y='Cumulative Net', markers=True, title=f"All-Time Net Flow ({freq})", color_discrete_sequence=[area_color_d])
                fig_net_d.update_traces(line_shape='spline') # This smooths the line and area
                fig_net_d.add_hline(y=0, line_dash="dash", line_color="gray")
                st.plotly_chart(fig_net_d, use_container_width=True, key=f"net_bal_plot_{domain_name}")

        with d_tabs[1]: # Expenditure
            exp_df = filt_dom[filt_dom['Transaction Type'].isin(['Expenditure', 'Paid'])]
            st.metric("Total Expenditure", f"₹{exp_df['Amount'].sum():,.2f}")
            render_flexible_plots(exp_df, f"exp_{domain_name}")
            st.dataframe(exp_df.sort_values('Date', ascending=False), use_container_width=True)

        with d_tabs[2]: # Income
            inc_df = filt_dom[filt_dom['Transaction Type'].isin(['Income', 'Received'])]
            st.metric("Total Income", f"₹{inc_df['Amount'].sum():,.2f}")
            render_flexible_plots(inc_df, f"inc_{domain_name}")
            st.dataframe(inc_df.sort_values('Date', ascending=False), use_container_width=True)

        with d_tabs[3]: # Manage
            # FIXED ERROR: Using domain_df_all instead of domain_df
            render_delete_interface(domain_df_all, domain_name) 

def render_funds_tab(data):
    df_raw = load_data()
    if df_raw.empty: 
        st.info("No data found.")
        return
        
    df_raw['Date'] = pd.to_datetime(df_raw['Date']).dt.date

    st.markdown("### ⏱️ Time Filter")
    time_period = st.selectbox("Select Duration", ["All Time", "This Month", "Last 3 Months", "This Year", "Custom Range"])
    today = date.today()
    start_date, end_date = df_raw['Date'].min(), df_raw['Date'].max()
    if time_period == "This Month": start_date = today.replace(day=1)
    elif time_period == "This Year": start_date = today.replace(month=1, day=1)
    
    # We still create the time-filtered df for the Global Income/Expenditure tabs
    df = df_raw[(df_raw['Date'] >= start_date) & (df_raw['Date'] <= end_date)].copy()
    tabs = st.tabs(["📊 Overview", "🟩 Income", "🟥 Expenditure", "💸 Loans", "🚗 Car", "🐄 Cows", "🐑 Sheep", "🌱 Agri", "🏠 Home", "🧍 Personal", "🤝 Friends"])

    # 1. GLOBAL OVERVIEW
    with tabs[0]: 
        master_all = get_clean_data(df_raw)
        filt_g_all = apply_dynamic_filters(master_all, "global")
        
        # Apply Time Filter for metrics
        mask_g = (filt_g_all['Date'] >= start_date) & (filt_g_all['Date'] <= end_date)
        filt_g = filt_g_all[mask_g]
        
        # Global Metrics
        inc_val = filt_g[filt_g['Transaction Type'].isin(['Income', 'Received'])]['Amount'].sum()
        exp_val = filt_g[filt_g['Transaction Type'].isin(['Expenditure', 'Paid'])]['Amount'].sum()
        g1, g2, g3 = st.columns(3)
        g1.metric("Global Income (Period)", f"₹{inc_val:,.2f}")
        g2.metric("Global Expenditure (Period)", f"₹{exp_val:,.2f}")
        g3.metric("Global Net Balance (Period)", f"₹{(inc_val - exp_val):,.2f}")
        
        # Periodic Global Time Series
        st.markdown("#### ⏳ Global Time Trend")
        tc1, tc2 = st.columns(2)
        with tc1: g_freq = st.selectbox("Frequency", ["Daily", "Weekly", "Monthly", "Quarterly"], key="g_freq_overview")
        with tc2: g_agg = st.selectbox("Metric", ["Sum", "Mean"], key="g_agg_overview")
        
        ts_g = filt_g.copy()
        ts_g['Date'] = pd.to_datetime(ts_g['Date'])
        freq_map = {"Daily": "D", "Weekly": "W", "Monthly": "ME", "Quarterly": "QE"}
        ts_res_g = ts_g.set_index('Date').groupby('Transaction Type').resample(freq_map[g_freq])['Amount'].agg(g_agg.lower()).reset_index()
        
        fig_g = px.line(ts_res_g, x='Date', y='Amount', color='Transaction Type', markers=True, title="Income vs Expenditure (Selected Period)")
        st.plotly_chart(fig_g, use_container_width=True, key="line_trend_global_overview")

        render_flexible_plots(filt_g, "global_overview")
        
        # --- CUMULATIVE GLOBAL NET BALANCE (ALL TIME SMOOTHED AREA) ---
        ts_g_all = filt_g_all.copy()
        ts_g_all['Date'] = pd.to_datetime(ts_g_all['Date'])
        ts_res_g_all = ts_g_all.set_index('Date').groupby('Transaction Type').resample(freq_map[g_freq])['Amount'].agg(g_agg.lower()).reset_index()

        if not ts_res_g_all.empty:
            st.markdown("#### 📉 Cumulative Global Net Balance (All-Time Net Flow)")
            net_df_g = ts_res_g_all.copy()
            net_df_g['Type'] = net_df_g['Transaction Type'].replace({'Received': 'Income', 'Paid': 'Expenditure'})
            net_pivot_g = net_df_g.pivot_table(index='Date', columns='Type', values='Amount', aggfunc='sum').fillna(0)
            for col in ['Income', 'Expenditure']:
                if col not in net_pivot_g.columns:
                    net_pivot_g[col] = 0
            
            # Calculate Running Cumulative Sum
            net_pivot_g['Net Balance'] = net_pivot_g['Income'] - net_pivot_g['Expenditure']
            net_pivot_g['Cumulative Net'] = net_pivot_g['Net Balance'].cumsum()
            net_pivot_g = net_pivot_g.reset_index()
            
            # Determine color based on current (latest) net value
            current_net_g = net_pivot_g['Cumulative Net'].iloc[-1] if not net_pivot_g.empty else 0
            if current_net_g < 0:
                area_color_g = '#EF553B' # Red
            elif current_net_g < 5000:
                area_color_g = '#636EFA' # Blue
            else:
                area_color_g = '#00CC96' # Green

            # Smoothed Area Plot
            fig_net_g = px.area(net_pivot_g, x='Date', y='Cumulative Net', markers=True, title=f"All-Time Global Net Flow ({g_freq})", color_discrete_sequence=[area_color_g])
            fig_net_g.update_traces(line_shape='spline') # Smooths the graph
            fig_net_g.add_hline(y=0, line_dash="dash", line_color="gray")
            st.plotly_chart(fig_net_g, use_container_width=True, key="net_bal_plot_global")

        st.dataframe(filt_g.sort_values('Date', ascending=False), use_container_width=True)

    # 2. GLOBAL INCOME
    with tabs[1]: 
        inc_df = get_clean_data(df[df['Transaction Type'].isin(['Income', 'Received'])])
        filt_inc = apply_dynamic_filters(inc_df, "global_inc")
        
        st.metric("Total Global Income", f"₹{filt_inc['Amount'].sum():,.2f}")
        
        if not filt_inc.empty:
            tc1, tc2 = st.columns(2)
            with tc1: i_freq = st.selectbox("Frequency", ["Daily", "Weekly", "Monthly", "Quarterly"], key="g_freq_inc")
            with tc2: i_agg = st.selectbox("Metric", ["Sum", "Mean"], key="g_agg_inc")
            
            ts_i = filt_inc.copy()
            ts_i['Date'] = pd.to_datetime(ts_i['Date'])
            ts_res_i = ts_i.set_index('Date').groupby('Domain').resample(freq_map[i_freq])['Amount'].agg(i_agg.lower()).reset_index()
            
            fig_i = px.line(ts_res_i, x='Date', y='Amount', color='Domain', markers=True, title="Income Trend by Domain")
            st.plotly_chart(fig_i, use_container_width=True, key="line_trend_global_inc")

        render_flexible_plots(filt_inc, "global_inc_plots")
        st.dataframe(filt_inc.sort_values('Date', ascending=False), use_container_width=True)

    # 3. GLOBAL EXPENDITURE
    with tabs[2]: 
        exp_df = get_clean_data(df[df['Transaction Type'].isin(['Expenditure', 'Paid'])])
        filt_exp = apply_dynamic_filters(exp_df, "global_exp")
        
        st.metric("Total Global Expenditure", f"₹{filt_exp['Amount'].sum():,.2f}")
        
        if not filt_exp.empty:
            tc1, tc2 = st.columns(2)
            with tc1: e_freq = st.selectbox("Frequency", ["Daily", "Weekly", "Monthly", "Quarterly"], key="g_freq_exp")
            with tc2: e_agg = st.selectbox("Metric", ["Sum", "Mean"], key="g_agg_exp")
            
            ts_e = filt_exp.copy()
            ts_e['Date'] = pd.to_datetime(ts_e['Date'])
            ts_res_e = ts_e.set_index('Date').groupby('Domain').resample(freq_map[e_freq])['Amount'].agg(e_agg.lower()).reset_index()
            
            fig_e = px.line(ts_res_e, x='Date', y='Amount', color='Domain', markers=True, title="Expenditure Trend by Domain")
            st.plotly_chart(fig_e, use_container_width=True, key="line_trend_global_exp")

        render_flexible_plots(filt_exp, "global_exp_plots")
        st.dataframe(filt_exp.sort_values('Date', ascending=False), use_container_width=True)

    # 4. DOMAIN DASHBOARDS
    dom_list = ["Car", "Cows", "Sheep", "Agri Land", "Home", "Personal", "Friends lending"]
    for i, d_name in enumerate(dom_list):
        # We pass df_raw directly into the domains to allow all-time cumulative math!
        render_domain_dashboard(d_name, tabs[i+4], df_raw, start_date, end_date)
