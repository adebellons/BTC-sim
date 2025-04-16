import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np

st.set_page_config(page_title="BTC Sim", layout="wide")
st.title("BTC Sim")

# Sidebar inputs
st.sidebar.header("Simulation Inputs")
initial_btc = st.sidebar.number_input("Initial BTC Amount", value=1.0, min_value=0.0)
initial_price = st.sidebar.number_input("Initial BTC Price (USD)", value=30000.0, min_value=0.0)
ltv = st.sidebar.slider("Loan-to-Value (LTV %)", min_value=0, max_value=100, value=50)
ltv_liquidation_percentage = st.sidebar.slider("LTV Liquidation Threshold (%)", min_value=0, max_value=100, value=80)  # New slider
interest_rate = st.sidebar.number_input("Loan Interest Rate (%)", value=5.0, min_value=0.0)
loan_term = st.sidebar.number_input("Loan Term (months)", value=12, min_value=1)
monthly_dca = st.sidebar.number_input("Monthly DCA Amount (BTC)", value=0.01)
monthly_withdrawal = st.sidebar.number_input("Monthly Income Withdrawal (USD)", value=500.0)
monthly_payment = st.sidebar.number_input("Monthly Payment (USD)", value=0.0, min_value=0.0)  # New input

use_historical_data = st.sidebar.checkbox("Use Historical Bitcoin Price Data for Prediction")

run_simulation = st.sidebar.button("Run Simulation")

if run_simulation:
    # Initial values
    btc_price = initial_price
    btc_balance = initial_btc
    loan_amount = initial_btc * initial_price * (ltv / 100)
    monthly_interest = interest_rate / 12 / 100
    
    # Fetch historical data if required
    if use_historical_data:
        st.sidebar.text("Fetching historical data...")
        data = yf.download('BTC-USD', period="5y", interval="1d")  # Fetch 5 years of historical data
        
        # Debugging: Check if data is returned
        if data.empty:
            st.error("Error: No data returned from Yahoo Finance. Please check the data source.")
        else:
            # Display a preview of the data to verify
            st.sidebar.text(f"Fetched {len(data)} days of historical data.")
            st.sidebar.text(f"Data preview:\n{data.head()}")

            historical_prices = data['Close']
            pct_changes = historical_prices.pct_change().dropna()
            
            # Check if pct_changes is not empty
            if pct_changes.empty:
                st.error("Error: No percentage changes calculated. Check historical data.")
            else:
                # Calculate the average percentage change, ensure it's a scalar
                avg_monthly_pct_change = pct_changes.mean()
                
                # Ensure avg_monthly_pct_change is a scalar and not a pandas Series
                if isinstance(avg_monthly_pct_change, pd.Series):
                    avg_monthly_pct_change = avg_monthly_pct_change.values[0]
                
                st.sidebar.text(f"Avg. Monthly Price Change (from historical data): {avg_monthly_pct_change * 100:.2f}%")
                
                # Predict future prices based on historical average change
                price_prediction = []
                for month in range(loan_term + 1):
                    btc_price *= (1 + avg_monthly_pct_change)  # Predict next month's price based on historical change
                    price_prediction.append(float(btc_price))  # Ensure it's a float, not a Series

                # Use the predicted price for the simulation
                btc_price = price_prediction[0]
    
    else:
        # If historical data is not used, simulate a manual monthly price change
        monthly_price_change = st.sidebar.number_input("BTC Monthly Price Change (%)", value=2.0)
        price_prediction = [btc_price]
        for month in range(loan_term + 1):
            btc_price *= (1 + monthly_price_change / 100)  # Simulate price change based on user input
            price_prediction.append(float(btc_price))  # Ensure it's a float, not a Series

    # Tracking
    data = []
    liquidation_triggered = False
    liquidation_month = None
    total_interest_accrued = 0.0  # Track total interest accrued

    for month in range(loan_term + 1):
        total_btc_value = btc_balance * price_prediction[month]
        monthly_interest_accrued = loan_amount * monthly_interest  # Monthly interest for the month
        total_interest_accrued += monthly_interest_accrued  # Add to total interest

        # Calculate minimum payment: minimum of interest or monthly payment
        minimum_payment = max(monthly_interest_accrued, monthly_payment)
        
        # If loan balance is zero, set minimum payment to zero
        if loan_amount <= 0:
            minimum_payment = 0

        # Calculate liquidation risk based on LTV liquidation percentage
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

        # Simulate next month
        loan_amount += monthly_withdrawal
        loan_amount += monthly_interest_accrued  # Add interest to loan balance

        # Apply the minimum payment to reduce the loan balance
        loan_amount -= minimum_payment

        # Ensure loan balance does not go below zero
        if loan_amount < 0:
            loan_amount = 0

    df = pd.DataFrame(data)

    # Full Simulation Data Table
    st.subheader("Full Simulation Data")
    st.dataframe(df.style.format({
        "BTC Price": "${:,.2f}",
        "BTC Value (USD)": "${:,.2f}",
        "Loan Balance (USD)": "${:,.2f}",
        "Interest Accrued (USD)": "${:,.2f}",
        "Monthly Interest (USD)": "${:,.2f}",
        "Minimum Payment (USD)": "${:,.2f}"
    }))

    # CSV download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "btc_sim_results.csv", "text/csv")

else:
    st.info("Enter values on the left and click 'Run Simulation' to see the results.")
