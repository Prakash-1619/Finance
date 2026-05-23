import streamlit as st
import pandas as pd
from datetime import date
import json
from github_sync import load_data, save_data_to_github

def render_form_tab():
    form_tabs = st.tabs(["💵 Financial Entry", "🔧 Service Entry (Placeholder)"])
    
    with form_tabs[1]:
        st.info("Service form fields will go here in the future.")
        
    with form_tabs[0]:
        st.subheader("Add New Transaction")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            entry_date = st.date_input("Transaction Date", date.today())
            trans_type = st.radio("Type", ["Expenditure", "Income", "Loans", "EMI"], horizontal=True)
            amount = st.number_input("Amount", min_value=0.0, step=100.0, format="%.2f")
            
        with col2:
            #currency = st.selectbox("Currency", ["INR (₹)", "USD ($)", "EUR (€)", "Other"])
            payment_status = st.selectbox("Payment Status", ["Completed / Received", "Partial / Remaining"])
            frequency = st.selectbox("Frequency", ["One-time", "Daily", "Weekly", "Monthly", "Annually", "None"]) if trans_type in ["Expenditure", "Income"] else "One-time"
            
        with col3:
            st.markdown("**Payment Route**")
            pay_app = st.selectbox("App/Method", ["BHIM", "PhonePe", "Paytm", "GPay", "Super Money","Slice", "None"])
            bank_name = st.selectbox("Bank", ["Indian Bank", "SBI", "FI/Federal", "AXIS", "Cash"])
            phone_num = st.selectbox("Number Used", ["9550927050", "7702486243", "Other"])

        st.markdown("**Entities & Description**")
        p_col1, p_col2, p_col3 = st.columns(3)
        with p_col1:
            person_org = st.text_input("Person Name")
        with p_col2:
            org_name = st.text_input("Organization Name")
        with p_col3:
            desc = st.text_input("Brief Description / Purpose")
            
        st.divider()

        # --- DOMAIN SPECIFIC LOGIC ---
        st.subheader("Domain Specifics")
        
        if trans_type == "Income": domain_list = ["Salary", "Car", "Sheep", "Personal", "Home", "Agri Land", "Loans", "Friends lending","Cows"]
        elif trans_type in ["Loans", "EMI"]: domain_list = [trans_type]
        else: domain_list = ["Car", "Sheep","Cows", "Personal", "Home", "Agri Land", "Friends lending"]

        domain = st.selectbox("Select Domain / Category", domain_list)
        sub_category = ""
        extra = {}
        if domain == "Sheep" and trans_type == "Income":
            sub_category = st.selectbox("Sheep Category", ["Selling", "Cutting", ])
            extra["Tag ID"] = st.text_input("Animal Tag ID(s)")
            extra["Count"] = st.text_input("Total Count")
            extra["Purchaser name"] = st.text_input("Name")
            extra["Total Weight (kg)"] = st.number_input("Weight (kg)", min_value=0.0)
            if sub_category == "Selling": extra["Cost Per Sheep"] = st.number_input("Selling price")
            if sub_category == "Selling": extra["Market name"] = st.text_input("Market name")
            if sub_category == "Cutting": extra["Price per KG"] = st.number_input("Selling price")

        elif domain == "Cows" and trans_type == "Income":
            sub_category = st.selectbox("Cows Category", ["Selling", "Milk", "Cow dung" ])
            extra["Tag ID"] = st.text_input("Animal Tag ID(s)")
            extra["Purchaser name"] = st.text_input("Name")
            extra["Total Weight (kg)"] = st.number_input("Weight (kg)", min_value=0.0)
            if sub_category == "Milk": extra["Total milk"] = st.number_input("Milk Qnt")
            if sub_category == "Selling": extra["Market name"] = st.text_input("Market name")
            if sub_category == "Cow dung": extra["Quantity"] = st.number_input("Quantity")
        elif domain == "Agri Land" and trans_type == "Income":
            extra["Plot"] = st.text_input("Enter the Plot Number")
            extra["Crop"] = st.text_input("Crop name")
            sub_category = st.selectbox("Agri Category", ["Fodder", "Vegetables", "Leafy Veggies","Fruits"])
            if sub_category in ["Vegetables", "Leafy Veggies","Fruits"]: extra["Quantity & Unit"] = st.text_input("Quantity (e.g., 5 Bags, 10 Liters)")
        elif domain == "Personal" and trans_type == "Income":
            extra["Details"] = st.text_input("Details")
                    
        elif domain == "Car" and trans_type != "Income":
            sub_category = st.selectbox("Car Category", ["Diesel", "Repair", "Service", "Washing", "Insurance", "Other"])
            extra["Shop/Org Name"] = st.text_input("Name ")
            if sub_category == "Diesel": extra["Current Odometer (KM)"] = st.number_input("Odometer Reading", min_value=89400)
            if sub_category == "Diesel": extra["Price per litre"] = st.number_input("Diesel Price")
            if sub_category == "Insurance": extra["Policy Renewal Date"] = str(st.date_input("Renewal Date", date.today()))
            
        elif domain == "Sheep" and trans_type != "Income":
            sub_category = st.selectbox("Sheep Category", ["Purchase", "Medical", "Labour", "Feed","Fodder", "Other"])
            extra["Tag ID"] = st.text_input("Animal Tag ID(s)")
            extra["Count"] = st.text_input("Total Count")
            extra["Total Weight (kg)"] = st.number_input("Weight (kg)", min_value=0.0)
            if sub_category == "Medical": extra["Doctor Name"] = st.text_input("Veterinarian Name")
            if sub_category == "Fodder": extra["Seller Name"] = st.text_input("Seller Name")
        elif domain == "Cows" and trans_type != "Income":
            sub_category = st.selectbox("Category", ["Purchase", "Medical", "Labour", "Feed", "Fodder", "Other"])
            extra["Tag ID"] = st.text_input("Animal Tag ID(s)")
            extra["Count"] = st.text_input("Total Count")
            extra["Total Weight (kg)"] = st.number_input("Weight (kg)", min_value=0.0)
            if sub_category == "Medical": extra["Doctor Name"] = st.text_input("Veterinarian Name")
            if sub_category == "Fodder": extra["Seller Name"] = st.text_input("Seller Name")
        elif domain == "Agri Land" and trans_type != "Income":
            extra["Plot"] = st.text_input("Enter the Plot Number")
            extra["Crop"] = st.text_input("Crop name")
            sub_category = st.selectbox("Agri Category", ["Fertilizers", "Pesticide", "Ploughing", "Labour", "Seeds/Plants", "Irrigation", "Fodder"])
            extra["Crop/Season"] = st.text_input("Crop Cycle or Season (e.g., Kharif Corn)")
            if sub_category in ["Fertilizers", "Pesticide", "Seeds/Plants", "Fodder"]: extra["Quantity & Unit"] = st.text_input("Quantity (e.g., 5 Bags, 10 Liters)")
        elif domain == "Personal" and trans_type != "Income":
            sub_category = st.selectbox("Personal Category", ["Food", "Fashion", "Health/Medical", "Subscriptions", "Education", "Gifts/Donations", "Recharge", "Other"])
            if sub_category in ["Recharge"]: extra["Mobile Number"] = st.text_input("Enter mobile number")
            if sub_category in ["Other"]: extra["Details"] = st.text_input("details")
        elif domain == "Home" and trans_type != "Received":
            sub_category = st.selectbox("Home Category", ["Household", "Parents", "Occasion/Event", "Appliance/Asset", "Repair","Electricity", "Recharge"])
            if sub_category in ["Appliance/Asset", "Repair"]: extra["Asset Name"] = st.text_input("Specific Asset (e.g., Washing Machine, Roof)")
            if sub_category in ["Recharge"]: extra["Mobile Number"] = st.text_input("Enter mobile number")
        elif domain == "Friends lending" and trans_type != "Income":
            sub_category = st.selectbox("Lending Detail", ["Lending Out", "Helping", "Other"])
            if sub_category != "Helping":
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

        st.divider()

        # --- SUBMIT & CONFIRMATION LOGIC ---
        st.markdown("### 💾 Finalize Entry")
        
        def reset_form(): st.session_state['confirm_save'] = False
        confirm = st.checkbox("I confirm that the details entered above are accurate.", key="confirm_save")

        action_col, msg_col = st.columns([1, 2])

        with action_col:
            save_clicked = st.button("💾 Save to GitHub", type="primary", use_container_width=True, disabled=not confirm, on_click=reset_form)

        if save_clicked:
            if amount <= 0 and trans_type not in ["Loans", "EMI"]:
                with msg_col: st.error("Please enter a valid amount.")
            else:
                with st.spinner("Syncing to GitHub..."):
                    new_data = pd.DataFrame([{
                        "Date": entry_date, "Transaction Type": trans_type, #"Currency": currency,
                        "Payment Status": payment_status, "Amount": amount, "Frequency": frequency,
                        "Payment App": pay_app, "Phone Number": phone_num, "Bank Name": bank_name,
                        "Person/Org Name": person_org, "Org Name": org_name, "Domain": domain, "Sub-Category": sub_category,
                        "Description": desc, "Extra Details": json.dumps(extra)
                    }])
                    
                    # 1. Pull the latest DB from GitHub
                    current_df = load_data()
                    
                    # 2. Append the new row
                    updated_df = pd.concat([current_df, new_data], ignore_index=True)
                    
                    # 3. Push it back
                    success = save_data_to_github(updated_df, commit_message=f"Added {domain} transaction")
                    
                    if success:
                        with msg_col: st.success(f"✅ Securely synced ₹{amount} to {domain} in GitHub!")
