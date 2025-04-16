import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

st.title("BTC Loan Leverage Simulator")

# --- Sidebar settings ---
st.sidebar.header("Simulation Settings")

initial_btc = st.sidebar.number_input("Initial BTC Amount", value=1.0)
ltv = st.sidebar.slider("Initial Loan-to-Value (LTV) %", min_value=0, max_value=100, value=50)
liq_threshold = st.sidebar.slider("Liquidation Threshold LTV %", 1, 100, 85)
interest_rate = st.sidebar.number_input("Annual Interest Rate (%)", value=6.0)
payment = st.sidebar.number_input("Monthly Payment (USD)", value=0.0)

# New: Toggle between Standard Loan and DCA
simulation_type = st.sidebar.radio("Simulation Type", ("Standard Loan", "DCA with Independent Loans"))

# New: Monthly DCA input (only for DCA strategy)
if simulation_type == "DCA with Independent Loans":
    monthly_dca_usd = st.sidebar.number_input("Monthly DCA Amount (USD)", value=100.0)

simulation_months = st.sidebar.slider("Simulation Duration (Months)", 12, 120, 36)

use_live_data = st.sidebar.checkbox("Use live BTC price", value=False)

if use_live_data:
    btc_price = yf.Ticker("BTC-USD").history(period="1d")['Close'].iloc[-1]
else:
    btc_price = st.sidebar.number_input("BTC Price (USD)", value=30000.0)

run_sim = st.button("Run Simulation")

# Simulation logic
if run_sim:
    months = simulation_months
    prices = [btc_price * (1 + 0.02)**(i / 12) for i in range(months + 1)]

    loan_balance = initial_btc * btc_price * ltv / 100
    btc_amount = initial_btc
    interest_accrued = 0.0

    rows = []

    if simulation_type == "Standard Loan":
        for m in range(months + 1):
            price_idx = prices[m]
            btc_value = btc_amount * price_idx

            # Only calculate interest and payments after month 0
            if m > 0:
                monthly_interest = loan_balance * (interest_rate / 100) / 12
                interest_accrued += monthly_interest
                actual_payment = payment
                loan_balance += monthly_interest - actual_payment
            else:
                monthly_interest = 0.0
                actual_payment = 0.0

            loan_balance = max(loan_balance, 0.0)

            # compute risk
            curr_ltv = (loan_balance / btc_value * 100) if btc_value > 0 else 0.0
            risk = "Yes" if (curr_ltv > liq_threshold and loan_balance > 0) else "No"

            rows.append({
                "Month": m,
                "BTC Price (USD)": price_idx,
                "Collateral Value (USD)": btc_value,
                "Loan Balance (USD)": loan_balance,
                "Interest Accrued (Total)": interest_accrued,
                "Monthly Interest": monthly_interest,
                "Monthly Payment": actual_payment,
                "LTV %": curr_ltv,
                "At Risk of Liquidation": risk
            })

    elif simulation_type == "DCA with Independent Loans":
        # Initialize variables for DCA
        total_btc_dca = initial_btc
        total_loan_balance = 0.0
        total_interest_accrued = 0.0

        for m in range(months + 1):
            price_idx = prices[m]
            btc_value = total_btc_dca * price_idx

            # Each month a new loan is added based on the DCA amount
            if m > 0:
                new_btc = monthly_dca_usd / price_idx
                new_loan_balance = new_btc * price_idx * ltv / 100
                total_btc_dca += new_btc  # Add new BTC from DCA

                # Calculate interest for the new loan
                new_monthly_interest = new_loan_balance * (interest_rate / 100) / 12
                total_interest_accrued += new_monthly_interest
                total_loan_balance += new_loan_balance

            else:
                new_monthly_interest = 0.0

            total_loan_balance = max(total_loan_balance, 0.0)

            # Compute risk
            curr_ltv = (total_loan_balance / btc_value * 100) if btc_value > 0 else 0.0
            risk = "Yes" if (curr_ltv > liq_threshold and total_loan_balance > 0) else "No"

            rows.append({
                "Month": m,
                "BTC Price (USD)": price_idx,
                "Collateral Value (USD)": btc_value,
                "Loan Balance (USD)": total_loan_balance,
                "Interest Accrued (Total)": total_interest_accrued,
                "Monthly Interest": new_monthly_interest,
                "Monthly Payment": 0.0,  # No fixed payment in DCA strategy
                "LTV %": curr_ltv,
                "At Risk of Liquidation": risk
            })

    # Display results
    df = pd.DataFrame(rows)

    st.subheader("Simulation Results")
    st.dataframe(df.style.format({
        "BTC Price (USD)": "${:,.2f}",
        "Collateral Value (USD)": "${:,.2f}",
        "Loan Balance (USD)": "${:,.2f}",
        "Interest Accrued (Total)": "${:,.2f}",
        "Monthly Interest": "${:,.2f}",
        "Monthly Payment": "${:,.2f}",
        "LTV %": "{:.2f}%"
    }), use_container_width=True)
