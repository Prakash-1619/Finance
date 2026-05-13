import streamlit as st
import pandas as pd
from datetime import date
import json

def render_form_tab(csv_file):
    st.header("Add New Entry")
    
    # --- CORE TRANSACTION DETAILS ---
    col1, col2 = st.columns(2)
    
    with col1:
        entry_date = st.date_input("Date", date.today())
        trans_type = st.radio("Transaction Type", ["Paid", "Received", "Loans", "EMI"])
        amount = st.number_input("Amount", min_value=0.0, step=100.0, format="%.2f")
        
        # Payment App & Bank Details
        st.markdown("**Payment Route**")
        pay_app = st.selectbox("Service Name / App", ["Phone pe", "Paytm", "G pay", "super money", "None"])
        phone_num = st.selectbox("Number Used", ["9550927050", "7702486243", "Other"])
        bank_name = st.selectbox("Bank Name", ["Indian", "SBI", "FI/Federal", "AXIS", "Cash"])

    with col2:
        st.markdown("**Entities & Frequencies**")
        person_name = st.text_input("Name of the Person")
        org_name = st.text_input("Name of Organization")
        desc = st.text_area("Brief Description / Purpose")
        
        frequency = "One-time"
        if trans_type == "Paid":
            frequency = st.selectbox("Frequency", ["One-time", "Daily", "Weekly", "Monthly", "Quarterly", "Annually"])
            
    st.divider()

    # --- DOMAIN SPECIFIC LOGIC ---
    st.subheader("Domain Specifics")
    
    # Determine the list of domains based on Transaction Type
    if trans_type == "Received":
        domain_list = ["Salary", "Car", "Sheep", "Personal", "Home", "Agri Land", "Loans", "Friends lending"]
    elif trans_type == "Loans":
        domain_list = ["Loans"]
    elif trans_type == "EMI":
        domain_list = ["EMI"]
    else:
        domain_list = ["Car", "Sheep", "Personal", "Home", "Agri Land", "Loans", "Friends lending", "EMI"]

    domain = st.selectbox("Select Domain / Source", domain_list)
    
    # Initialize variables to capture specific details
    sub_category = ""
    extra_details = {}

    # Logic trees matching your form sections
    if domain == "Car" and trans_type != "Received":
        sub_category = st.selectbox("Car Category", ["Repair", "Service", "Washing", "Diesel", "Other"])
        extra_details["Car Name"] = st.text_input("Car Name")
        if sub_category == "Diesel":
            extra_details["KM"] = st.text_input("Mention KM")
        extra_details["Price"] = st.text_input("Mention Price")
        extra_details["Details"] = st.text_area("Car Details")

    elif domain == "Sheep" and trans_type != "Received":
        extra_details["Action Date"] = str(st.date_input("Sheep Date", date.today()))
        sub_category = st.selectbox("Sheep Category", ["Purchase", "Medical", "Labour", "Other"])
        if sub_category == "Medical":
            extra_details["Doctor"] = st.text_input("Doctor Name")
        extra_details["Details"] = st.text_area("Sheep Details")

    elif domain == "Personal" and trans_type != "Received":
        sub_category = st.selectbox("Personal Category", ["Food", "Fashion", "Option 3"])

    elif domain == "Home" and trans_type != "Received":
        sub_category = st.selectbox("Home Category", ["Occasion", "Event", "Parents", "House hold", "Other"])

    elif domain == "Agri Land" and trans_type != "Received":
        sub_category = st.selectbox("Agri Category", ["Fodder", "Ploughing", "Plants", "Labour", "Pipe and irrigation", "Pesticide", "Fertilizers", "Other"])

    elif domain == "Friends lending" and trans_type != "Received":
        extra_details["Purpose"] = st.text_input("Purpose")
        sub_category = st.selectbox("Trans Details", ["Returning", "Help", "Other"])
        if sub_category == "Returning":
            extra_details["Returning Date"] = str(st.date_input("When Returning?", date.today()))

    elif domain == "Loans":
        extra_details["Loan Date"] = str(st.date_input("Loan Date", date.today()))
        sub_category = st.selectbox("Asset", ["Gold", "Car", "Land", "Personal", "Business"])
        extra_details["Interest"] = st.text_input("Interest Rate/Amount")
        extra_details["Tenure (Months)"] = st.text_input("Tenure (In months)")
        extra_details["Loan Details"] = st.text_area("Loan specifics")

    elif domain == "EMI":
        sub_category = st.selectbox("Loan Type", ["Personal", "Other"])
        extra_details["Interest"] = st.text_input("Interest")
        extra_details["Loan Name"] = st.text_input("Loan Name")
        extra_details["EMI per month"] = st.text_input("EMI per month")
        extra_details["EMI Date"] = st.text_input("EMI Date (e.g., 5th of every month)")
        extra_details["Tenure"] = st.text_input("Tenure")

    # --- SUBMIT LOGIC ---
    if st.button("💾 Save Entry", type="primary", use_container_width=True):
        if amount <= 0 and trans_type not in ["Loans", "EMI"]:
            # Allow zero amount for Loans/EMI if you are just logging the contract, otherwise enforce > 0
            st.error("Please enter a valid amount.")
        else:
            # Combine person and org name for the CSV
            person_org = f"{person_name} ({org_name})" if org_name else person_name
            
            new_data = pd.DataFrame([{
                "Date": entry_date,
                "Transaction Type": trans_type,
                "Amount": amount,
                "Frequency": frequency,
                "Payment App": pay_app,
                "Phone Number": phone_num,
                "Bank Name": bank_name,
                "Person/Org Name": person_org,
                "Domain": domain,
                "Sub-Category": sub_category,
                "Description": desc,
                "Extra Details": json.dumps(extra_details) # Saves dictionary as a readable string
            }])
            
            new_data.to_csv(csv_file, mode='a', header=False, index=False)
            st.success("✅ Transaction Saved Successfully!")
            st.rerun()
