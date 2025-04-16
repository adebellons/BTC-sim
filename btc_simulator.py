import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

st.title("BTC Loan Leverage Simulator")

# --- Inputs ---
st.sidebar.header("Initial Settings")
initial_btc = st.sidebar.number_input("Initial BTC Amount", value=1.0, step=0.01)
initial_price = st.sidebar.number_input("Initial BTC Price (USD)", value=50000.0, step=100.0)
ltv = st.sidebar.slider("Loan-to-Value (LTV %)", min_value=10, max_value=90, value=50)
interest_rate = st.sidebar.number_input("Annual Interest Rate (%)", value=6.0, step=0.1)
loan_term = st.sidebar.number_input("Loan Term (Months)", value=12, step=1)
monthly_payment = st.sidebar.number_input("Monthly Payment (USD)", value=100.0, step=10.0)
min_monthly_payment = st.sidebar.number_input("Minimum Monthly Payment (USD)", value=0.0, step=10.0)
liq_threshold = st.sidebar.slider("Liquidation Threshold LTV (%)", min_value=50, max_value=100, value=85)

st.sidebar.header("DCA Settings")
dca_enabled = st.sidebar.checkbox("Enable DCA", value=False)
dca_monthly_usd = st.sidebar.number_input("Monthly DCA Amount (USD)", value=100.0, step=10.0)

st.sidebar.header("Bitcoin Price Source")
price_mode = st.sidebar.radio("Use BTC Price Data From:", ("Live", "Historical"))
if price_mode == "Historical":
    start_date = st.sidebar.date_input("Start Date", value=datetime(2021, 1, 1))
    end_date = st.sidebar.date_input("End Date", value=datetime(2022, 1, 1))
    btc_hist = yf.download("BTC-USD", start=start_date, end=end_date, interval="1mo")
    btc_prices = btc_hist["Close"].tolist()
else:
    btc_prices = [initial_price * (1 + 0.02 * ((-1) ** i)) for i in range(loan_term)]

# --- Run Simulation ---
if st.button("Run Simulation"):
    rows = []
    btc_amount = initial_btc
    btc_price = btc_prices[0]
    loan_balance = btc_price * btc_amount * (ltv / 100)
    total_interest = 0.0

    for m in range(loan_term + 1):
        price_idx = btc_prices[m] if m < len(btc_prices) else btc_prices[-1]
        btc_value = btc_amount * price_idx

        # Interest for this month
        interest = loan_balance * (interest_rate / 100) / 12 if m > 0 else 0.0
        total_interest += interest

        # Determine monthly payment to apply
        payment = monthly_payment if m > 0 else 0.0
        payment = max(payment, min_monthly_payment)

        # Update loan balance
        if m > 0:
            loan_balance += interest
            loan_balance -= payment
            loan_balance = max(loan_balance, 0.0)

        # current LTV for liquidation
        curr_ltv = (loan_balance / float(btc_value) * 100) if float(btc_value) > 0 else 0
        risk = "Yes" if (curr_ltv > liq_threshold and loan_balance > 0) else "No"

        rows.append({
            "Month": m,
            "BTC Price (USD)": price_idx,
            "BTC Value (USD)": btc_value,
            "Loan Balance (USD)": loan_balance,
            "Interest Accrued (Total)": total_interest,
            "Risk of Liquidation": risk
        })

        # Apply DCA
        if dca_enabled and m > 0:
            added_btc = dca_monthly_usd / price_idx
            btc_amount += added_btc

    df = pd.DataFrame(rows)

    st.subheader("Simulation Results")
    st.dataframe(df.style.format({
        "BTC Price (USD)": "${:,.2f}",
        "BTC Value (USD)": "${:,.2f}",
        "Loan Balance (USD)": "${:,.2f}",
        "Interest Accrued (Total)": "${:,.2f}"
    }))
