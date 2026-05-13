import streamlit as st
import pandas as pd
from datetime import date

def render_form_tab(csv_file):
    st.header("Add New Transaction")
    
    # Layout with columns for a cleaner look
    col1, col2 = st.columns(2)
    
    with col1:
        entry_date = st.date_input("Date", date.today())
        trans_type = st.radio("Transaction Type", ["Paid (Expense)", "Received (Income)", "Loan/EMI"])
        amount = st.number_input("Amount", min_value=0.0, step=100.0, format="%.2f")
        pay_method = st.selectbox("Account / Payment Method", ["SBI", "Axis", "Indian Bank", "UPI (PhonePe/GPay)", "Cash"])
    
    with col2:
        domain = st.selectbox("Domain", ["General Funds", "Personal", "Car", "Sheep", "Agri Land", "Home", "Friends Lending"])
        
        # Dynamic Sub-categories based on Domain selection
        category = ""
        extra_details = ""
        
        if domain == "Car":
            category = st.selectbox("Car Category", ["Diesel", "Repair", "Service", "Washing", "Other"])
            if category == "Diesel":
                extra_details = st.text_input("Current Odometer Reading (KM)")
                
        elif domain == "Sheep":
            category = st.selectbox("Sheep Category", ["Purchase", "Medical", "Labour", "Feed", "Other"])
            if category == "Medical":
                extra_details = st.text_input("Doctor Name / Medicine Details")
                
        elif domain == "Agri Land":
            category = st.selectbox("Agri Category", ["Fodder", "Ploughing", "Plants", "Labour", "Irrigation", "Pesticide", "Fertilizers"])
            
        elif domain == "Personal":
            category = st.selectbox("Personal Category", ["Food", "Fashion", "Health", "Subscriptions"])
            
        else:
            category = st.text_input("Category (Optional)")
            
        desc = st.text_area("Description / Purpose")

    # Submit Button
    if st.button("💾 Save Entry", type="primary", use_container_width=True):
        if amount <= 0:
            st.error("Please enter a valid amount.")
        else:
            # Create a new record
            new_data = pd.DataFrame([{
                "Date": entry_date,
                "Transaction Type": trans_type,
                "Domain": domain,
                "Category": category,
                "Amount": amount,
                "Payment Method": pay_method,
                "Description": desc,
                "Extra Details": extra_details
            }])
            
            # Append to CSV
            new_data.to_csv(csv_file, mode='a', header=False, index=False)
            st.success("✅ Transaction Saved Successfully!")
            st.rerun() # Refresh the page to clear inputs
