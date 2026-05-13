import streamlit as st
import pandas as pd
import plotly.express as px

def render_funds_tab(csv_file):
    st.header("Funds & Balance Sheet")
    
    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        st.error("Could not load data.")
        return

    if df.empty:
        st.info("No data available yet. Please add entries in the Data Entry Form.")
        return

    # Convert Date column to datetime for filtering
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # --- FILTERS ---
    st.subheader("Filters")
    col1, col2 = st.columns(2)
    with col1:
        selected_domains = st.multiselect("Filter by Domain", options=df['Domain'].unique(), default=df['Domain'].unique())
    with col2:
        selected_types = st.multiselect("Filter by Type", options=df['Transaction Type'].unique(), default=df['Transaction Type'].unique())

    # Apply filters
    filtered_df = df[(df['Domain'].isin(selected_domains)) & (df['Transaction Type'].isin(selected_types))]

    # --- BALANCE SHEET KPIs ---
    st.subheader("Balance Sheet Overview")
    income = df[df['Transaction Type'] == 'Received (Income)']['Amount'].sum()
    expense = df[df['Transaction Type'] == 'Paid (Expense)']['Amount'].sum()
    balance = income - expense

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Income 🟩", f"₹ {income:,.2f}")
    m2.metric("Total Expense 🟥", f"₹ {expense:,.2f}")
    m3.metric("Net Balance 🟦", f"₹ {balance:,.2f}")

    st.divider()

    # --- PLOTS ---
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("**Expenses by Domain**")
        expense_df = filtered_df[filtered_df['Transaction Type'] == 'Paid (Expense)']
        if not expense_df.empty:
            fig_pie = px.pie(expense_df, values='Amount', names='Domain', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.write("No expense data for selected filters.")

    with col4:
        st.markdown("**Income vs Expense (Timeline)**")
        # Group by date and type
        timeline_df = filtered_df.groupby([filtered_df['Date'].dt.date, 'Transaction Type'])['Amount'].sum().reset_index()
        if not timeline_df.empty:
            fig_bar = px.bar(timeline_df, x='Date', y='Amount', color='Transaction Type', barmode='group')
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.write("No timeline data available.")

    # --- RAW DATA TABLE ---
    st.subheader("Transaction History")
    # Sort by date descending
    st.dataframe(filtered_df.sort_values(by="Date", ascending=False), use_container_width=True, hide_index=True)
