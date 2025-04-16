import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

st.set_page_config(page_title="BTC Loan Leverage Simulator", layout="wide")

st.title("Bitcoin Loan Leverage Simulator")

# Sidebar inputs
st.sidebar.header("Simulation Settings")

initial_btc = st.sidebar.number_input("Initial BTC Amount", value=1.0, step=0.01)
ltv_ratio = st.sidebar.slider("Initial LTV (%)", min_value=0, max_value=100, value=50)
interest_rate = st.sidebar.number_input("Annual Interest Rate (%)", value=6.0, step=0.1)
monthly_payment = st.sidebar.number_input("Monthly Loan Payment (USD)", value=0.0, step=10.0)
min_monthly_payment = st.sidebar.number_input("Minimum Monthly Payment (USD)", value=0.0, step=10.0)
liq_threshold = st.sidebar.slider("Liquidation LTV Threshold (%)", min_value=0, max_value=100, value=85)
loan_term_months = st.sidebar.number_input("Loan Term (Months)", value=36, step=1)
monthly_dca_usd = st.sidebar.number_input("Monthly DCA (USD)", value=0.0, step=10.0)

# Bitcoin price source
price_source = st.sidebar.radio("Bitcoin Price Source", ["Historical", "Live"], index=0)

if price_source == "Historical":
    start_date = st.sidebar.date_input("Start Date", value=datetime(2020, 1, 1))
    end_date = st.sidebar.date_input("End Date", value=datetime.today())
    btc_data = yf.download("BTC-USD", start=start_date, end=end_date, progress=False)
    if btc_data.empty:
        st.error("No BTC price data available for selected date range.")
        st.stop()
    btc_prices = btc_data["Close"].resample("M").last().ffill()
else:
    # Simulate future prices using a simple growth model
    current_price = yf.download("BTC-USD", period="1d")["Close"].iloc[-1]
    btc_prices = pd.Series(
        [current_price * (1 + 0.02) ** i for i in range(loan_term_months + 1)]
    )
    btc_prices.index = pd.date_range(datetime.today(), periods=loan_term_months + 1, freq="M")

# Run Simulation button
run_sim = st.button("Run Simulation")

if run_sim:
    rows = []
    btc_amount = initial_btc
    price_list = btc_prices.tolist()

    # Initial loan amount based on LTV
    initial_loan = btc_amount * price_list[0] * (ltv_ratio / 100)
    loan_balance = initial_loan
    total_interest = 0

    for m in range(len(price_list)):
        price_idx = price_list[m]
        btc_value = float(btc_amount * price_idx)

        # Interest
        interest = loan_balance * (interest_rate / 100 / 12) if m > 0 else 0

        # Total payment
        payment = max(monthly_payment, min_monthly_payment) if m > 0 else 0

        # Update loan balance
        if m > 0:
            loan_balance += interest - payment
            loan_balance = max(loan_balance, 0.0)
            total_interest += interest

        # current LTV for liquidation
        curr_ltv = (loan_balance / btc_value * 100) if btc_value != 0 else 0
        risk = "Yes" if (curr_ltv > liq_threshold and loan_balance > 0) else "No"

        rows.append({
            "Month": m,
            "BTC Price (USD)": price_idx,
            "BTC Value (USD)": btc_value,
            "Loan Balance (USD)": loan_balance,
            "Interest Accrued (Total)": total_interest,
            "Monthly Payment": payment,
            "Current LTV (%)": curr_ltv,
            "At Risk of Liquidation": risk,
        })

        # Add new BTC from DCA
        if monthly_dca_usd > 0:
            btc_amount += monthly_dca_usd / price_idx

    df = pd.DataFrame(rows)

    st.subheader("Simulation Results")
    st.dataframe(df.style.format({
        "BTC Price (USD)": "${:,.2f}",
        "BTC Value (USD)": "${:,.2f}",
        "Loan Balance (USD)": "${:,.2f}",
        "Interest Accrued (Total)": "${:,.2f}",
        "Monthly Payment": "${:,.2f}",
        "Current LTV (%)": "{:.2f}%"
    }))
