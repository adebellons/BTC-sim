import streamlit as st
import pandas as pd

st.set_page_config(page_title="BTC Sim", layout="wide")
st.title("BTC Sim")

# Sidebar inputs
st.sidebar.header("Simulation Inputs")
initial_btc = st.sidebar.number_input("Initial BTC Amount", value=1.0, min_value=0.0)
initial_price = st.sidebar.number_input("Initial BTC Price (USD)", value=30000.0, min_value=0.0)
ltv = st.sidebar.slider("Loan-to-Value (LTV %)", min_value=0, max_value=100, value=50)
ltv_liquidation_percentage = st.sidebar.slider("LTV Liquidation Threshold (%)", min_value=0, max_value=100, value=80)  # New slider
interest_rate = st.sidebar.number_input("Loan Interest Rate (%)", value=5.0, min_value=0.0)
loan_term = st.sidebar.number_input("Loan Term (months)", value=12, min_value=1)
monthly_price_change = st.sidebar.number_input("BTC Monthly Price Change (%)", value=2.0)
monthly_dca = st.sidebar.number_input("Monthly DCA Amount (BTC)", value=0.01)
monthly_withdrawal = st.sidebar.number_input("Monthly Income Withdrawal (USD)", value=500.0)
monthly_payment = st.sidebar.number_input("Monthly Payment (USD)", value=0.0, min_value=0.0)  # New input

run_simulation = st.sidebar.button("Run Simulation")

if run_simulation:
    # Initial values
    btc_price = initial_price
    btc_balance = initial_btc
    loan_amount = initial_btc * initial_price * (ltv / 100)
    monthly_interest = interest_rate / 12 / 100

    # Tracking
    data = []
    liquidation_triggered = False
    liquidation_month = None
    total_interest_accrued = 0.0  # Track total interest accrued

    for month in range(loan_term + 1):
        total_btc_value = btc_balance * btc_price
        interest_accrued = loan_amount * monthly_interest  # Interest for the month
        total_interest_accrued += interest_accrued  # Add to total interest

        # Calculate minimum payment: minimum of interest or monthly payment
        minimum_payment = max(interest_accrued, monthly_payment)
        
        # If loan balance is zero, set minimum payment to zero
        if loan_amount <= 0:
            minimum_payment = 0

        # Calculate liquidation risk based on LTV liquidation percentage
        if total_btc_value < loan_amount * (ltv_liquidation_percentage / 100):
            liquidation_risk = "Yes"
        else:
            liquidation_risk = "No"

        if not liquidation_triggered and total_btc_value < loan_amount:
            liquidation_triggered = True
            liquidation_month = month

        data.append({
            "Month": month,
            "BTC Price": btc_price,
            "BTC Balance": btc_balance,
            "BTC Value (USD)": total_btc_value,
            "Loan Balance (USD)": loan_amount,
            "Interest Accrued (USD)": total_interest_accrued,
            "Minimum Payment (USD)": minimum_payment,
            "Liquidation Risk": liquidation_risk
        })

        # Simulate next month
        btc_price *= (1 + monthly_price_change / 100)
        btc_balance += monthly_dca
        loan_amount += monthly_withdrawal
        loan_amount += interest_accrued  # Add interest to loan balance

        # Apply the minimum payment to reduce the loan balance
        loan_amount -= minimum_payment

        # Ensure loan balance does not go below zero
        if loan_amount < 0:
            loan_amount = 0

    df = pd.DataFrame(data)

    # Full Simulation Data Table
    st.subheader("Full Simulation Data")
    st.dataframe(df.style.format({
        "BTC Price": "${:,.2f}",
        "BTC Value (USD)": "${:,.2f}",
        "Loan Balance (USD)": "${:,.2f}",
        "Interest Accrued (USD)": "${:,.2f}",
        "Minimum Payment (USD)": "${:,.2f}"
    }))

    # CSV download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "btc_sim_results.csv", "text/csv")

else:
    st.info("Enter values on the left and click 'Run Simulation' to see the results.")
