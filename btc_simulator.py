import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="BTC Loan Leverage Simulator", layout="wide")
st.title("BTC Loan Leverage Simulator")

# Sidebar inputs
st.sidebar.header("Simulation Inputs")

# Move Run Simulation button to the top
run_simulation = st.sidebar.button("Run Simulation")

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
monthly_dca = st.sidebar.number_input("Monthly DCA Amount (BTC)", value=0.01)
monthly_withdrawal = st.sidebar.number_input("Monthly Income Withdrawal (USD)", value=500.0)
monthly_payment = st.sidebar.number_input("Monthly Payment (USD)", value=0.0, min_value=0.0)

if run_simulation:
    # Initial values and setup
    btc_price = initial_price
    btc_balance = initial_btc
    loan_balance = initial_btc * btc_price * (ltv / 100)  # Initial loan balance based on LTV
    loan_amount = loan_balance  # This is the amount we are borrowing (LTV based)
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

    # Prepare the data structure to hold the simulation results
    data = []
    total_interest_accrued = 0.0

    for month in range(loan_term + 1):
        btc_price = price_prediction[month]
        btc_balance += monthly_dca
        total_btc_value = btc_balance * btc_price  # Correct BTC value calculation

        # For month 0, skip interest and payment calculation
        if month > 0:
            # Calculate interest based on loan balance
            monthly_interest_accrued = loan_amount * monthly_interest
            total_interest_accrued += monthly_interest_accrued

            # Calculate the minimum payment (interest + principal repayment)
            minimum_payment = max(monthly_interest_accrued, monthly_payment)
            if loan_amount <= 0:
                minimum_payment = 0
        else:
            monthly_interest_accrued = 0
            minimum_payment = 0

        # Loan balance is calculated as LTV of the BTC value
        loan_balance = total_btc_value * (ltv / 100)

        # Update loan balance after subtracting the monthly payment
        if month > 0:  # Start applying payments from month 1
            loan_balance -= minimum_payment
            if loan_balance < 0:
                loan_balance = 0  # Ensure the loan balance doesn't go negative

        # Update the loan amount with interest and withdrawal
        loan_amount += monthly_withdrawal + monthly_interest_accrued
        loan_amount -= minimum_payment
        if loan_amount < 0:
            loan_amount = 0

        # Liquidation risk calculation
        if total_btc_value < loan_balance * (ltv_liquidation_percentage / 100):
            liquidation_risk = "Yes"
        else:
            liquidation_risk = "No"

        # Append monthly data to the results
        data.append({
            "Month": month,
            "BTC Price": btc_price,
            "BTC Balance": btc_balance,
            "BTC Value (USD)": total_btc_value,  # Correct BTC value column
            "Loan Balance (USD)": loan_balance,  # Correct Loan Balance calculation reflecting payments
            "Interest Accrued (USD)": total_interest_accrued,
            "Monthly Interest (USD)": monthly_interest_accrued,
            "Monthly Payment (USD)": minimum_payment,
            "Liquidation Risk": liquidation_risk
        })

    # Convert the data to a dataframe for display
    df = pd.DataFrame(data)

    st.subheader("Simulation Results")
    st.dataframe(df.style.format({
        "BTC Price": "${:,.2f}",
        "BTC Value (USD)": "${:,.2f}",
        "Loan Balance (USD)": "${:,.2f}",
        "Interest Accrued (USD)": "${:,.2f}",
        "Monthly Interest (USD)": "${:,.2f}",
        "Monthly Payment (USD)": "${:,.2f}"
    }))

    # CSV Download Button
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "btc_sim_results.csv", "text/csv")

else:
    st.info("Enter values on the left and click 'Run Simulation' to see the results.")
