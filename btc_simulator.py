import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="BTC Loan Leverage Simulator", layout="wide")
st.title("BTC Loan Leverage Simulator")

# Sidebar inputs
st.sidebar.header("Simulation Inputs")
run_simulation = st.sidebar.button("Run Simulation")

initial_btc = st.sidebar.number_input("Initial BTC Amount", value=1.0, min_value=0.0)
use_historical_data = st.sidebar.checkbox("Use Historical Bitcoin Price Data for Prediction")
use_live_price = st.sidebar.checkbox("Use Live Bitcoin Price")

live_price = None
if use_live_price:
    st.sidebar.write("Fetching live Bitcoin price...")
    try:
        live_price = yf.Ticker("BTC-USD").history(period="1d")['Close'].iloc[-1]
        st.sidebar.write(f"Live Bitcoin Price: ${live_price:,.2f}")
    except Exception as e:
        st.sidebar.error(f"Error fetching live price: {e}")

initial_price = st.sidebar.number_input("Initial BTC Price (USD)", value=30000.0, min_value=0.0)
ltv = st.sidebar.slider("Loan-to-Value (LTV %)", min_value=0, max_value=100, value=50)
liq_threshold = st.sidebar.slider("LTV Liquidation Threshold (%)", min_value=0, max_value=100, value=80)
interest_rate = st.sidebar.number_input("Loan Interest Rate (%)", value=5.0, min_value=0.0)
loan_term = st.sidebar.number_input("Loan Term (months)", value=12, min_value=1)
monthly_dca = st.sidebar.number_input("Monthly DCA Amount (BTC)", value=0.01)
monthly_payment_input = st.sidebar.number_input("Monthly Payment (USD)", value=0.0, min_value=0.0)

if run_simulation:
    # Pricing model
    price_series = []
    if use_live_price and live_price:
        price_series.append(float(live_price))
        if use_historical_data:
            data = yf.download('BTC-USD', period="5y", interval="1d")
            if not data.empty:
                avg_pct_change = data['Close'].pct_change().mean()
                for _ in range(loan_term):
                    price_series.append(price_series[-1] * (1 + avg_pct_change))
        else:
            monthly_price_change = st.sidebar.number_input("BTC Monthly Price Change (%)", value=2.0)
            for _ in range(loan_term):
                price_series.append(price_series[-1] * (1 + monthly_price_change / 100))
    elif use_historical_data:
        data = yf.download('BTC-USD', period="5y", interval="1d")
        if not data.empty:
            avg_pct_change = data['Close'].pct_change().mean()
            price_series = [initial_price]
            for _ in range(loan_term):
                price_series.append(price_series[-1] * (1 + avg_pct_change))
    else:
        price_series = [initial_price]
        monthly_price_change = st.sidebar.number_input("BTC Monthly Price Change (%)", value=2.0)
        for _ in range(loan_term):
            price_series.append(price_series[-1] * (1 + monthly_price_change / 100))

    # Loan simulation
    btc_balance = initial_btc
    monthly_int = interest_rate / 12 / 100
    loan_balance = initial_btc * price_series[0] * (ltv / 100)
    total_interest = 0.0
    rows = []

    for m in range(loan_term + 1):
        btc_balance += monthly_dca
        btc_price = price_series[m]
        btc_value = btc_balance * btc_price

        if m == 0:
            interest = 0.0
            payment  = 0.0
        else:
            interest = float(loan_balance * monthly_int)
            total_interest += interest
            payment  = max(interest, monthly_payment_input)
            loan_balance = loan_balance + interest - payment
            loan_balance = max(loan_balance, 0.0)

        # current LTV for liquidation
        curr_ltv = (loan_balance / btc_value * 100) if btc_value > 0 else 0
        risk = "Yes" if (curr_ltv > liq_threshold and loan_balance > 0) else "No"

        rows.append({
            "Month": m,
            "BTC Price (USD)": btc_price,
            "BTC Balance": btc_balance,
            "BTC Value (USD)": btc_value,
            "Loan Balance (USD)": loan_balance,
            "Interest Accrued (Total)": total_interest,
            "Monthly Interest (USD)": interest,
            "Monthly Payment (USD)": payment,
            "Liquidation Risk": risk
        })

    df = pd.DataFrame(rows)

    st.subheader("Simulation Results")
    st.dataframe(df.style.format({
        "BTC Price (USD)": "${:,.2f}",
        "BTC Value (USD)": "${:,.2f}",
        "Loan Balance (USD)": "${:,.2f}",
        "Interest Accrued (Total)": "${:,.2f}",
        "Monthly Interest (USD)": "${:,.2f}",
        "Monthly Payment (USD)": "${:,.2f}"
    }))

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "btc_sim_results.csv", "text/csv")
else:
    st.info("Enter values on the left and click 'Run Simulation' to see the results.")
