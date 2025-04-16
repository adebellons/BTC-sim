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
min_payment = st.sidebar.number_input("Minimum Monthly Payment (USD)", value=0.0)

simulation_months = st.sidebar.slider("Simulation Duration (Months)", 12, 120, 36)

use_live_data = st.sidebar.checkbox("Use live BTC price", value=False)

if use_live_data:
    btc_price = yf.Ticker("BTC-USD").history(period="1d")['Close'].iloc[-1]
else:
    btc_price = st.sidebar.number_input("BTC Price (USD)", value=30000.0)

run_sim = st.button("Run Simulation")

if run_sim:
    months = simulation_months
    prices = [btc_price * (1 + 0.02)**(i / 12) for i in range(months + 1)]

    loan_balance = initial_btc * btc_price * ltv / 100
    btc_amount = initial_btc
    interest_accrued = 0.0

    rows = []

    for m in range(months + 1):
        price_idx = prices[m]
        btc_value = btc_amount * price_idx

        # Only calculate interest and payments after month 0
        if m > 0:
            monthly_interest = loan_balance * (interest_rate / 100) / 12
            interest_accrued += monthly_interest
            actual_payment = max(payment, min_payment)
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
