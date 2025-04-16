import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np

st.set_page_config(page_title="BTC Sim", layout="wide")
st.title("BTC Sim")

# Sidebar inputs
st.sidebar.header("Simulation Inputs")
initial_btc = st.sidebar.number_input("Initial BTC Amount", value=1.0, min_value=0.0)

# Moved checkboxes directly under initial BTC input
use_historical_data = st.sidebar.checkbox("Use Historical Bitcoin Price Data for Prediction")
use_live_price = st.sidebar.checkbox("Use Live Bitcoin Price")

initial_price = st.sidebar.number_input("Initial BTC Price (USD)", value=30000.0, min_value=0.0)
ltv = st.sidebar.slider("Loan-to-Value (LTV %)", min_value=0, max_value=100, value=50)
ltv_liquidation_percentage = st.sidebar.slider("LTV Liquidation Threshold (%)", min_value=0, max_value=100, value=80)
interest_rate = st.sidebar.number_input("Loan Interest Rate (%)", value=5.0, min_value=0.0)
loan_term = st.sidebar.number_input("Loan Term (months)", value=12, min_value=1)
monthly_dca = st.sidebar.number_input("Monthly DCA Amount (BTC)", value=0.01)
monthly_withdrawal = st.sidebar.number_input("Monthly Income Withdrawal (USD)", value=500.0)
monthly_payment = st.sidebar.number_input("Monthly Payment (USD)", value=0.0, min_value=0.0)

run_simulation = st.sidebar.button("Run Simulation")

if run_simulation:
    btc_price = initial_price
    btc_balance = initial_btc
    loan_amount = initial_btc * initial_price * (ltv / 100)
    monthly_interest = interest_rate / 12 / 100
    price_prediction = [btc_price]

    if use_live_price:
        st.sidebar.text("Fetching live Bitcoin price...")
        btc_price = yf.Ticker("BTC-USD").history(period="1d")['Close'].iloc[-1]
        st.sidebar.text(f"Live Bitcoin Price: ${btc_price:.2f}")
        price_prediction[0] = btc_price

    elif use_historical_data:
        data = yf.download('BTC-USD', period="5y", interval="1d")
        if data.empty:
            st.error("Error: No data returned from Yahoo Finance.")
        else:
            historical_prices = data['Close']
            pct_changes = historical_prices.pct_change().dropna()
            if pct_changes.empty:
                st.error("Error: No percentage changes calculated.")
            else:
                avg_monthly_pct_change = pct_changes.mean()
                if isinstance(avg_monthly_pct_change, pd.Series):
                    avg_monthly_pct_change = avg_monthly_pct_change.values[0]
                for month in range(loan_term + 1):
                    btc_price *= (1 + avg_monthly_pct_change)
                    price_prediction.append(float(btc_price))
    else:
        monthly_price_change = st.sidebar.number_input("BTC Monthly Price Change (%)", value=2.0)
        for month in range(loan_term + 1):
            btc_price *= (1 + monthly_price_change / 100)
            price_prediction.append(float(btc_price))

    while len(price_prediction) < loan_term + 1:
        price_prediction.append(price_prediction[-1])

    data = []
    liquidation_triggered = False
    liquidation_month = None
    total_interest_accrued = 0.0

    for month in range(loan_term + 1):
        total_btc_value = btc_balance * price_prediction[month]
        monthly_interest_accrued = loan_amount * monthly_interest
        total_interest_accrued += monthly_interest_accrued

        minimum_payment = max(monthly_interest_accrued, monthly_payment)
        if loan_amount <= 0:
            minimum_payment = 0

        if total_btc_value < loan_amount * (ltv_liquidation_percentage / 100):
            liquidation_risk = "Yes"
        else:
            liquidation_risk = "No"

        if not liquidation_triggered and total_btc_value < loan_amount:
            liquidation_triggered = True
            liquidation_month = month

        data.append({
            "Month": month,
            "BTC Price": price_prediction[month],
            "BTC Balance": btc_balance,
            "BTC Value (USD)": total_btc_value,
            "Loan Balance (USD)": loan_amount,
            "Interest Accrued (USD)": total_interest_accrued,
            "Monthly Interest (USD)": monthly_interest_accrued,
            "Minimum Payment (USD)": minimum_payment,
            "Liquidation Risk": liquidation_risk
        })

        loan_amount += monthly_withdrawal
        loan_amount += monthly_interest_accrued
        loan_amount -= minimum_payment
        if loan_amount < 0:
            loan_amount = 0

    df = pd.DataFrame(data)

    st.subheader("Full Simulation Data")
    st.dataframe(df.style.format({
        "BTC Price": "${:,.2f}",
        "BTC Value (USD)": "${:,.2f}",
        "Loan Balance (USD)": "${:,.2f}",
        "Interest Accrued (USD)": "${:,.2f}",
        "Monthly Interest (USD)": "${:,.2f}",
        "Minimum Payment (USD)": "${:,.2f}"
    }))

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "btc_sim_results.csv", "text/csv")

else:
    st.info("Enter values on the left and click 'Run Simulation' to see the results.")
