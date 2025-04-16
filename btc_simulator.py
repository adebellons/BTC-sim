import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

st.set_page_config(page_title="BTC Loan Leverage Simulator", layout="wide")
st.title("BTC Loan Leverage Simulator")

with st.sidebar:
    st.header("Simulation Settings")

    sim_type = st.radio("Price Data", ["Historical", "Live"], index=0)
    if sim_type == "Historical":
        years = st.slider("Years of Historical Data", 1, 10, 5)
    else:
        years = 1

    initial_btc = st.number_input("Initial BTC Collateral", min_value=0.0, value=1.0)
    initial_price = st.number_input("Initial BTC Price (USD)", min_value=1.0, value=30000.0)

    ltv = st.slider("Loan-to-Value (LTV %)", min_value=10, max_value=90, value=50, step=1)
    interest_rate = st.number_input("Annual Interest Rate (%)", min_value=0.0, value=6.0)
    monthly_payment = st.number_input("Monthly Payment (USD)", min_value=0.0, value=0.0)
    min_payment = st.number_input("Minimum Monthly Payment (USD)", min_value=0.0, value=0.0)
    liq_threshold = st.slider("Liquidation Threshold (%)", min_value=1, max_value=100, value=85, step=1)

    dca_enabled = st.checkbox("Enable DCA (BTC)", value=False)
    if dca_enabled:
        dca_btc = st.number_input("Monthly DCA Amount (in USD)", min_value=0.0, value=100.0)

run_sim = st.button("Run Simulation")

if run_sim:
    if sim_type == "Historical":
        btc_data = yf.download("BTC-USD", period=f"{years}y", interval="1mo")["Close"].dropna().reset_index()
        price_series = btc_data["Close"].tolist()
    else:
        price_series = [initial_price * (1 + np.random.normal(0, 0.05)) for _ in range(years * 12)]

    loan_amount = initial_btc * initial_price * (ltv / 100)
    btc_total = initial_btc
    loan_balance = loan_amount
    total_interest = 0.0

    rows = []

    for m, price in enumerate(price_series):
        btc_value = btc_total * price
        monthly_interest = (interest_rate / 100) / 12 * loan_balance if m > 0 else 0.0
        total_interest += monthly_interest

        actual_payment = max(monthly_payment, min_payment) if m > 0 else 0.0
        loan_balance = loan_balance + monthly_interest - actual_payment
        loan_balance = max(loan_balance, 0.0)

        if dca_enabled:
            btc_total += dca_btc / price

        curr_ltv = (loan_balance / btc_value * 100) if btc_value > 0 else 0.0
        risk = "Yes" if (curr_ltv > liq_threshold and loan_balance > 0) else "No"

        rows.append({
            "Month": m,
            "BTC Price (USD)": price,
            "Collateral Value (USD)": btc_value,
            "Loan Balance (USD)": loan_balance,
            "Interest Accrued (Total)": total_interest,
            "Monthly Payment": actual_payment,
            "Monthly Interest": monthly_interest,
            "LTV (%)": curr_ltv,
            "Risk of Liquidation": risk,
        })

    df = pd.DataFrame(rows)

    st.subheader("Simulation Results")
    st.dataframe(df.style.format({
        "BTC Price (USD)": "${:,.2f}",
        "Collateral Value (USD)": "${:,.2f}",
        "Loan Balance (USD)": "${:,.2f}",
        "Interest Accrued (Total)": "${:,.2f}",
        "Monthly Payment": "${:,.2f}",
        "Monthly Interest": "${:,.2f}",
        "LTV (%)": "{:.2f}%",
    }))
