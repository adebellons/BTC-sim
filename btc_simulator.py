import streamlit as st
import pandas as pd
import yfinance as yf
import datetime

st.set_page_config(page_title="BTC Loan Leverage Simulator")

st.title("BTC Loan Leverage Simulator")

st.sidebar.header("Simulation Settings")

# Simulation parameters
initial_btc = st.sidebar.number_input("Initial BTC Amount", value=1.0)
initial_price = st.sidebar.number_input("Initial BTC Price (USD)", value=30000.0)
ltv_ratio = st.sidebar.slider("Loan-to-Value (LTV) Ratio (%)", min_value=0, max_value=100, value=50)
liquidation_threshold = st.sidebar.slider("Liquidation Threshold (%)", min_value=0, max_value=100, value=80)
loan_term = st.sidebar.number_input("Loan Term (Months)", value=12)
annual_interest_rate = st.sidebar.number_input("Annual Interest Rate (%)", value=6.0)
monthly_withdrawal = st.sidebar.number_input("Monthly Loan Withdrawal (USD)", value=0.0)
monthly_payment = st.sidebar.number_input("Monthly Loan Payment (USD)", value=0.0)
monthly_dca_usd = st.sidebar.number_input("Monthly DCA Purchase (USD)", value=0.0)

# Historical data or live price toggle
use_historical = st.sidebar.checkbox("Use Historical BTC Data for Prediction")
use_live_price = st.sidebar.checkbox("Use Live BTC Price")

# Run button at the top
run_simulation = st.button("Run Simulation")

if run_simulation:
    # Fetch live BTC price if selected
    if use_live_price:
        st.sidebar.text("Fetching live Bitcoin price...")
        live_data = yf.download("BTC-USD", period="1d", interval="1m")
        if not live_data.empty:
            live_price = live_data['Close'][-1]
            st.sidebar.text(f"Live Bitcoin Price: ${live_price:,.2f}")
            initial_price = live_price

    # Generate price predictions
    price_prediction = []

    if use_historical:
        end_date = datetime.datetime.today()
        start_date = end_date - datetime.timedelta(days=5 * 365)  # Last 5 years
        hist_data = yf.download("BTC-USD", start=start_date, end=end_date, interval='1mo')
        monthly_closes = hist_data["Close"]

        pct_changes = monthly_closes.pct_change().dropna()
        if pct_changes.empty:
            st.error("Error: No percentage changes calculated. Check historical data.")
        else:
            avg_monthly_pct_change = pct_changes.mean()
            for i in range(loan_term + 1):
                if i == 0:
                    price_prediction.append(initial_price)
                else:
                    next_price = price_prediction[-1] * (1 + avg_monthly_pct_change)
                    price_prediction.append(next_price)
    else:
        for i in range(loan_term + 1):
            price_prediction.append(initial_price)  # Flat price by default

    btc_balance = initial_btc
    loan_amount = initial_price * initial_btc * (ltv_ratio / 100)
    monthly_interest = annual_interest_rate / 12 / 100
    liquidation_month = None
    total_interest_accrued = 0.0
    simulation_data = []

    for month in range(loan_term + 1):
        btc_balance += monthly_dca_usd / price_prediction[month]

        total_btc_value = btc_balance * price_prediction[month]
        monthly_interest_accrued = loan_amount * monthly_interest
        total_interest_accrued += monthly_interest_accrued

        # Monthly payment and minimum payment start at month 0 again
        minimum_payment = max(monthly_interest_accrued, monthly_payment)
        if loan_amount <= 0:
            minimum_payment = 0

        loan_amount += monthly_withdrawal + monthly_interest_accrued
        loan_amount -= minimum_payment

        if loan_amount < 0:
            loan_amount = 0

        ltv = (loan_amount / total_btc_value) * 100 if total_btc_value > 0 else 0
        liquidation_risk = "Yes" if ltv > liquidation_threshold and loan_amount > 0 else "No"

        if liquidation_risk == "Yes" and liquidation_month is None:
            liquidation_month = month

        simulation_data.append({
            "Month": month,
            "BTC Price (USD)": round(price_prediction[month], 2),
            "BTC Balance": round(btc_balance, 6),
            "Loan Balance (USD)": round(loan_amount, 2),
            "Monthly Interest": round(monthly_interest_accrued, 2),
            "Interest Accrued (Total)": round(total_interest_accrued, 2),
            "Monthly Payment": round(monthly_payment, 2),
            "Minimum Monthly Payment": round(minimum_payment, 2),
            "LTV (%)": round(ltv, 2),
            "Liquidation Risk": liquidation_risk
        })

    df = pd.DataFrame(simulation_data)
    st.subheader("Simulation Results (Standard Loan)")
    st.dataframe(df)

    if liquidation_month is not None:
        st.warning(f"⚠️ Liquidation risk triggered in month {liquidation_month}.")
