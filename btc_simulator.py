import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="BTC Loan Leverage Simulator", layout="wide")
st.title("BTC Loan Leverage Simulator")

# Run simulation button moved to the top
run_simulation = st.button("Run Simulation")

# Sidebar inputs
st.sidebar.header("Simulation Inputs")
initial_btc = st.sidebar.number_input("Initial BTC Amount", value=1.0, min_value=0.0)

# Checkboxes directly under initial BTC
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
ltv_liquidation_percentage = st.sidebar.slider("LTV Liquidation Threshold (%)", min_value=0, max_value=100, value=80)
interest_rate = st.sidebar.number_input("Loan Interest Rate (%)", value=5.0, min_value=0.0)
loan_term = st.sidebar.number_input("Loan Term (months)", value=12, min_value=1)
monthly_dca_usd = st.sidebar.number_input("Monthly DCA Amount (USD)", value=500.0)
monthly_withdrawal = st.sidebar.number_input("Monthly Income Withdrawal (USD)", value=500.0)
monthly_payment = st.sidebar.number_input("Monthly Payment (USD)", value=0.0, min_value=0.0)

# Loan type selection
loan_type = st.sidebar.selectbox("Loan Type", ["Standard Loan", "DCA as Independent Loans"])

if run_simulation:
    btc_price = initial_price
    btc_balance = initial_btc
    loan_amount = initial_btc * btc_price * (ltv / 100)
    monthly_interest = interest_rate / 12 / 100
    price_prediction = []

    if use_live_price and live_price:
        price_prediction.append(float(live_price))

        if use_historical_data:
            data = yf.download('BTC-USD', period="5y", interval="1d")
            if not data.empty:
                pct_changes = data['Close'].pct_change().dropna()
                if not pct_changes.empty:
                    avg_pct_change = pct_changes.mean()
                    if isinstance(avg_pct_change, pd.Series):
                        avg_pct_change = avg_pct_change.values[0]
                    btc_price = live_price
                    for _ in range(loan_term):
                        btc_price *= (1 + avg_pct_change)
                        price_prediction.append(float(btc_price))
        else:
            monthly_price_change = st.sidebar.number_input("BTC Monthly Price Change (%)", value=2.0)
            btc_price = live_price
            for _ in range(loan_term):
                btc_price *= (1 + monthly_price_change / 100)
                price_prediction.append(float(btc_price))

    elif use_historical_data:
        btc_price = initial_price
        price_prediction.append(btc_price)
        data = yf.download('BTC-USD', period="5y", interval="1d")
        if not data.empty:
            pct_changes = data['Close'].pct_change().dropna()
            if not pct_changes.empty:
                avg_pct_change = pct_changes.mean()
                if isinstance(avg_pct_change, pd.Series):
                    avg_pct_change = avg_pct_change.values[0]
                for _ in range(loan_term):
                    btc_price *= (1 + avg_pct_change)
                    price_prediction.append(float(btc_price))

    else:
        btc_price = initial_price
        price_prediction.append(btc_price)
        monthly_price_change = st.sidebar.number_input("BTC Monthly Price Change (%)", value=2.0)
        for _ in range(loan_term):
            btc_price *= (1 + monthly_price_change / 100)
            price_prediction.append(float(btc_price))

    while len(price_prediction) < loan_term + 1:
        price_prediction.append(price_prediction[-1])

    data = []
    total_interest_accrued = 0.0

    if loan_type == "Standard Loan":
        # Standard loan logic
        for month in range(loan_term + 1):
            btc_price = price_prediction[month]
            btc_balance += monthly_dca_usd / btc_price  # Convert DCA from USD to BTC
            total_btc_value = btc_balance * btc_price
            monthly_interest_accrued = loan_amount * monthly_interest
            total_interest_accrued += monthly_interest_accrued

            # Calculate the minimum payment
            minimum_payment = max(monthly_interest_accrued, monthly_payment)
            if loan_amount <= 0:
                minimum_payment = 0

            if total_btc_value < loan_amount * (ltv_liquidation_percentage / 100):
                liquidation_risk = "Yes"
            else:
                liquidation_risk = "No"

            # Add data for each month
            data.append({
                "Month": month,
                "BTC Price": btc_price,
                "BTC Balance": btc_balance,
                "BTC Value (USD)": total_btc_value,
                "Loan Balance (USD)": loan_amount,
                "Interest Accrued (USD)": total_interest_accrued,
                "Monthly Interest (USD)": monthly_interest_accrued,
                "Monthly Payment (USD)": monthly_payment,
                "Calculated Minimum Payment (USD)": minimum_payment,
                "Liquidation Risk": liquidation_risk
            })

            # Update loan amount based on payments
            loan_amount += monthly_withdrawal + monthly_interest_accrued
            loan_amount -= minimum_payment
            if loan_amount < 0:
                loan_amount = 0

    elif loan_type == "DCA as Independent Loans":
        # DCA as Independent Loans logic
        dca_loans = []
        total_interest_accrued = 0.0
        for month in range(loan_term + 1):
            btc_price = price_prediction[month]
            # Each DCA is treated as an independent loan
            loan_amount = monthly_dca_usd / btc_price * btc_price * (ltv / 100)  # Convert DCA from USD to BTC
            monthly_interest_accrued = loan_amount * monthly_interest
            total_interest_accrued += monthly_interest_accrued

            # Calculate the minimum payment
            minimum_payment = max(monthly_interest_accrued, monthly_payment)
            if loan_amount <= 0:
                minimum_payment = 0

            # Track each DCA loan's progress
            dca_loans.append({
                "Month": month,
                "BTC Price": btc_price,
                "DCA Loan Amount (USD)": loan_amount,
                "Interest Accrued (USD)": total_interest_accrued,
                "Monthly Interest (USD)": monthly_interest_accrued,
                "Monthly Payment (USD)": monthly_payment,
                "Calculated Minimum Payment (USD)": minimum_payment
            })

            # Update loan amount based on payments
            loan_amount -= minimum_payment
            if loan_amount < 0:
                loan_amount = 0

        # Flatten data for DCA loans into a DataFrame
        df_dca = pd.DataFrame(dca_loans)

        st.subheader("DCA as Independent Loans Results")
        st.dataframe(df_dca.style.format({
            "BTC Price": "${:,.2f}",
            "DCA Loan Amount (USD)": "${:,.2f}",
            "Interest Accrued (USD)": "${:,.2f}",
            "Monthly Interest (USD)": "${:,.2f}",
            "Monthly Payment (USD)": "${:,.2f}",
            "Calculated Minimum Payment (USD)": "${:,.2f}"
        }))

    df = pd.DataFrame(data)

    st.subheader("Standard Loan Results")
    st.dataframe(df.style.format({
        "BTC Price": "${:,.2f}",
        "BTC Value (USD)": "${:,.2f}",
        "Loan Balance (USD)": "${:,.2f}",
        "Interest Accrued (USD)": "${:,.2f}",
        "Monthly Interest (USD)": "${:,.2f}",
        "Monthly Payment (USD)": "${:,.2f}",
        "Calculated Minimum Payment (USD)": "${:,.2f}"
    }))

    # Option to download CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV (Standard Loan)", csv, "btc_sim_results_standard_loan.csv", "text/csv")

else:
    st.info("Enter values on the left and click 'Run Simulation' to see the results.")
