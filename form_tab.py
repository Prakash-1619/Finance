import streamlit as st
import pandas as pd
from datetime import date
import json

def render_form_tab(csv_file):
    # Form Sub-Tabs
    form_tabs = st.tabs(["💵 Financial Entry", "🔧 Service Entry (Placeholder)"])
    
    with form_tabs[1]:
        st.info("Service form fields will go here in the future.")
        
    with form_tabs[0]:
        st.subheader("Add New Transaction")
        
        # --- 1. CORE TRANSACTION DETAILS ---
        col1, col2, col3 = st.columns(3)
        with col1:
            entry_date = st.date_input("Transaction Date", date.today())
            trans_type = st.radio("Type", ["Paid", "Received", "Loans", "EMI"], horizontal=True)
            amount = st.number_input("Amount", min_value=0.0, step=100.0, format="%.2f")
            
        with col2:
            currency = st.selectbox("Currency", ["INR (₹)", "USD ($)", "EUR (€)", "Other"])
            payment_status = st.selectbox("Payment Status", ["Completed / Received", "Pending / Expected"])
            frequency = st.selectbox("Frequency", ["One-time", "Daily", "Weekly", "Monthly", "Annually"]) if trans_type in ["Paid", "Received"] else "One-time"
            
        with col3:
            st.markdown("**Payment Route**")
            pay_app = st.selectbox("App/Method", ["PhonePe", "Paytm", "GPay", "Super Money", "None"])
            bank_name = st.selectbox("Bank", ["Indian Bank", "SBI", "FI/Federal", "AXIS", "Cash"])
            phone_num = st.selectbox("Number Used", ["9550927050", "7702486243", "Other"])

        st.markdown("**Entities & Description**")
        p_col1, p_col2 = st.columns(2)
        with p_col1:
            person_org = st.text_input("Person or Organization Name")
        with p_col2:
            desc = st.text_input("Brief Description / Purpose")
            
        st.divider()

        # --- 2. DOMAIN SPECIFIC LOGIC ---
        st.subheader("Domain Specifics")
        
        if trans_type == "Received":
            domain_list = ["Salary", "Car", "Sheep", "Personal", "Home", "Agri Land", "Loans", "Friends lending"]
        elif trans_type in ["Loans", "EMI"]:
            domain_list = [trans_type]
        else:
            domain_list = ["Car", "Sheep", "Personal", "Home", "Agri Land", "Friends lending"]

        domain = st.selectbox("Select Domain / Category", domain_list)
        
        sub_category = ""
        extra = {}

        # DYNAMIC LOGIC GATES
        if domain == "Car" and trans_type != "Received":
            sub_category = st.selectbox("Car Category", ["Diesel", "Repair", "Service", "Washing", "Insurance", "Other"])
            extra["Car Name"] = st.text_input("Car Name")
            if sub_category == "Diesel":
                extra["Current Odometer (KM)"] = st.number_input("Odometer Reading", min_value=0)
            if sub_category == "Insurance":
                extra["Policy Renewal Date"] = str(st.date_input("Renewal Date", date.today()))

        elif domain == "Sheep" and trans_type != "Received":
            sub_category = st.selectbox("Sheep Category", ["Purchase", "Medical", "Labour", "Feed", "Other"])
            extra["Tag ID / Count"] = st.text_input("Animal Tag ID(s) or Total Count")
            extra["Total Weight (kg)"] = st.number_input("Weight (kg)", min_value=0.0)
            if sub_category == "Medical":
                extra["Doctor Name"] = st.text_input("Veterinarian Name")

        elif domain == "Agri Land" and trans_type != "Received":
            sub_category = st.selectbox("Agri Category", ["Fertilizers", "Pesticide", "Ploughing", "Labour", "Seeds/Plants", "Irrigation", "Fodder"])
            extra["Crop/Season"] = st.text_input("Crop Cycle or Season (e.g., Kharif Corn)")
            if sub_category in ["Fertilizers", "Pesticide", "Seeds/Plants", "Fodder"]:
                extra["Quantity & Unit"] = st.text_input("Quantity (e.g., 5 Bags, 10 Liters)")

        elif domain == "Personal" and trans_type != "Received":
            sub_category = st.selectbox("Personal Category", ["Food", "Fashion", "Health/Medical", "Subscriptions", "Education", "Gifts/Donations"])

        elif domain == "Home" and trans_type != "Received":
            sub_category = st.selectbox("Home Category", ["Household", "Parents", "Occasion/Event", "Appliance/Asset", "Repair"])
            if sub_category in ["Appliance/Asset", "Repair"]:
                extra["Asset Name"] = st.text_input("Specific Asset (e.g., Washing Machine, Roof)")

        elif domain == "Friends lending" and trans_type != "Received":
            sub_category = st.selectbox("Lending Detail", ["Lending Out", "Helping", "Other"])
            extra["Agreed Return Amount"] = st.number_input("Expected Return Amount", min_value=0.0)
            extra["Expected Return Date"] = str(st.date_input("When Returning?", date.today()))
            extra["Send Reminder?"] = st.selectbox("Needs Reminder?", ["Yes", "No"])

        elif domain == "Loans":
            sub_category = st.selectbox("Asset Loan Against", ["Gold", "Car", "Land", "Personal", "Business"])
            extra["Interest Type"] = st.selectbox("Interest Type", ["Flat Rate", "Reducing Balance"])
            extra["Interest Rate/Amt"] = st.text_input("Interest Rate")
            extra["Tenure (Months)"] = st.number_input("Tenure (Months)", min_value=1)
            extra["Projected End Date"] = str(st.date_input("End Date", date.today()))

        elif domain == "EMI":
            sub_category = st.selectbox("Loan Type", ["Personal", "Vehicle", "Home", "Other"])
            extra["Loan Name"] = st.text_input("Loan Name")
            extra["Next Due Date"] = str(st.date_input("Next EMI Due Date", date.today()))
            extra["Tenure Remaining"] = st.text_input("Months Remaining")

        # --- SUBMIT ---
        if st.button("💾 Save Record", type="primary", use_container_width=True):
            if amount <= 0 and trans_type not in ["Loans", "EMI"]:
                st.error("Please enter a valid amount.")
            else:
                new_data = pd.DataFrame([{
                    "Date": entry_date, "Transaction Type": trans_type, "Currency": currency,
                    "Payment Status": payment_status, "Amount": amount, "Frequency": frequency,
                    "Payment App": pay_app, "Phone Number": phone_num, "Bank Name": bank_name,
                    "Person/Org Name": person_org, "Domain": domain, "Sub-Category": sub_category,
                    "Description": desc, "Extra Details": json.dumps(extra)
                }])
                new_data.to_csv(csv_file, mode='a', header=False, index=False)
                st.success(f"✅ Record Saved to {domain} successfully!")
                st.rerun()
