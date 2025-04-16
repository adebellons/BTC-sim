import streamlit as st
import pandas as pd

# Set initial parameters
initial_btc_balance = st.number_input("Initial BTC Balance", min_value=0.0, value=1.0)
btc_price = st.number_input("Current BTC Price (USD)", min_value=0.0, value=40000.0)
ltv = st.number_input("Loan-to-Value (LTV) Ratio (%)", min_value=0.0, max_value=100.0, value=50.0)
interest_rate = st.number_input("Annual Interest Rate (%)", min_value=0.0, value=5.0)
months = st.number_input("Months for Simulation", min_value=1, value=12)
monthly_payment = st.number_input("Monthly Payment (USD)", min_value=0.0, value=1000.0)

# Calculating the initial loan balance based on LTV ratio
btc_value = initial_btc_balance * btc_price
initial_loan_balance = btc_value * (ltv / 100)

# Prepare list to store simulation data
rows = []

# Initial values for month 0
loan_balance = initial_loan_balance
total_interest = 0
interest_accrued = 0

# Run simulation for each month
for m in range(0, months):
    # For month 0, initialize values
    if m == 0:
        loan_balance = initial_loan_balance  # no payments or interest for month 0
        interest_accrued = 0
        total_interest = 0
        monthly_payment = 0
    else:
        # Month 1 onwards: calculate interest and payments
        interest_accrued = loan_balance * interest_rate / 100 / 12  # Monthly interest
        total_interest += interest_accrued
        loan_balance = loan_balance + interest_accrued - monthly_payment  # Subtract payment
        loan_balance = max(loan_balance, 0)  # Prevent loan balance from going negative

    # Calculate risk and update table rows (this remains the same)
    curr_ltv = (loan_balance / btc_value * 100) if btc_value > 0 else 0
    risk = "Yes" if (curr_ltv > ltv and loan_balance > 0) else "No"

    # Store monthly data
    rows.append({
        "Month": m,
        "BTC Price (USD)": btc_price,
        "Collateral Value (USD)": btc_value,  # Rename this to Collateral Value
        "Loan Balance (USD)": loan_balance,
        "Interest Accrued (Total)": total_interest,
        "Monthly Payment (USD)": monthly_payment,
        "Risk of Liquidation": risk
    })

# Create DataFrame from simulation data
df = pd.DataFrame(rows)

# Display simulation results
st.subheader("Simulation Results")
st.dataframe(df.style.format({
    "BTC Price (USD)": "${:,.2f}",
    "Collateral Value (USD)": "${:,.2f}",
    "Loan Balance (USD)": "${:,.2f}",
    "Interest Accrued (Total)": "${:,.2f}",
    "Monthly Payment (USD)": "${:,.2f}",
}))

