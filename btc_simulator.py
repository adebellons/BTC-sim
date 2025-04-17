import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

st.title("BTC Loan Leverage Simulator")

# --- Sidebar settings ---
st.sidebar.header("Simulation Settings")

collateral_type = st.sidebar.radio("Select Initial Collateral Type", ("BTC", "USD"))

if collateral_type == "BTC":
    initial_btc = st.sidebar.number_input("Initial BTC Amount", value=1.0)
    initial_usd = None
else:
    initial_usd = st.sidebar.number_input("Initial USD Collateral Amount", value=30000.0)
    initial_btc = None

ltv = st.sidebar.slider("Initial Loan-to-Value (LTV) %", min_value=0, max_value=100, value=50)
liq_threshold = st.sidebar.slider("Liquidation Threshold LTV %", 1, 100, 85)
interest_rate = st.sidebar.number_input("Annual Interest Rate (%)", value=6.0)
payment = st.sidebar.number_input("Monthly Payment (USD)", value=0.0)

simulation_months = st.sidebar.slider("Simulation Duration (Months)", 12, 120, 36)

use_live_data = st.sidebar.checkbox("Use live BTC price", value=False)

dca_mode = st.sidebar.checkbox("DCA with Independent Loans", value=False)
if dca_mode:
    dca_amount = st.sidebar.number_input("Monthly DCA Amount (USD)", value=500.0)

if use_live_data:
    btc_price = yf.Ticker("BTC-USD").history(period="1d")['Close'].iloc[-1]
else:
    btc_price = st.sidebar.number_input("BTC Price (USD)", value=30000.0)

run_sim = st.button("Run Simulation")

if run_sim:
    months = simulation_months
    prices = [btc_price * (1 + 0.02)**(i / 12) for i in range(months + 1)]

    if not dca_mode:
        if initial_btc is not None:
            btc_amount = initial_btc
        else:
            btc_amount = initial_usd / btc_price

        loan_balance = btc_amount * btc_price * ltv / 100
        interest_accrued = 0.0

        rows = []

        for m in range(months + 1):
            price_idx = prices[m]
            btc_value = btc_amount * price_idx

            if m > 0:
                monthly_interest = loan_balance * (interest_rate / 100) / 12
                interest_accrued += monthly_interest
                actual_payment = payment
                loan_balance += monthly_interest - actual_payment
            else:
                monthly_interest = 0.0
                actual_payment = 0.0

            loan_balance = max(loan_balance, 0.0)

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
                "At Risk of Liquidation": risk,
                "Total Loan Balance (USD)": loan_balance  # Initially it's just the loan balance
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
            "LTV %": "{:.2f}%",
            "Total Loan Balance (USD)": "${:,.2f}"
        }), use_container_width=True)

    else:
        loan_history = []
        active_loans = []

        for m in range(1, months + 1):
            price = prices[m]

            if m == 1:
                btc_purchased = initial_usd / price
                collateral_value = initial_usd
            else:
                btc_purchased = dca_amount / price
                collateral_value = dca_amount

            loan_amount = collateral_value * ltv / 100
            monthly_interest_rate = (interest_rate / 100) / 12

            if active_loans:
                payment_to_previous = loan_amount * 0.10
                active_loans[-1]['payment'] += payment_to_previous
            else:
                payment_to_previous = 0.0

            new_loan = {
                "loan_id": len(active_loans) + 1,
                "start_month": m,
                "btc_collateral": btc_purchased,
                "loan_balance": loan_amount,
                "payment": 0.0,
                "interest_accrued": 0.0
            }
            active_loans.append(new_loan)

            # Calculate total loan balance for this month
            total_loan_balance = 0.0
            for loan in active_loans:
                if m >= loan['start_month']:
                    num_active_loans = len([l for l in active_loans if m >= l['start_month']])
                    monthly_share_payment = payment / num_active_loans if num_active_loans > 0 else 0.0

                    if m == loan['start_month']:
                        # No payment or interest for the first month of each loan
                        interest = 0.0
                        total_payment = 0.0
                    else:
                        interest = loan['loan_balance'] * monthly_interest_rate
                        loan['interest_accrued'] += interest
                        loan['loan_balance'] += interest - loan['payment'] - monthly_share_payment
                        loan['loan_balance'] = max(loan['loan_balance'], 0.0)
                        total_payment = loan['payment'] + monthly_share_payment

                    # Summing the loan balances to calculate total loan balance
                    total_loan_balance += loan['loan_balance']

                    ltv_percent = loan['loan_balance'] / (loan['btc_collateral'] * price) * 100
                    at_risk = "Yes" if ltv_percent > liq_threshold else "No"

                    # Add the total loan balance for all loans for the last loan of each month
                    if loan == active_loans[-1]:
                        loan_history.append({
                            "Month": m,
                            "Loan #": loan['loan_id'],
                            "BTC Price (USD)": price,
                            "Collateral Value (USD)": loan['btc_collateral'] * price,
                            "Loan Balance (USD)": loan['loan_balance'],
                            "Interest Accrued (Total)": loan['interest_accrued'],
                            "Monthly Payment": total_payment,
                            "LTV %": ltv_percent,
                            "At Risk of Liquidation": at_risk,
                            "Total Loan Balance (USD)": total_loan_balance  # Only the last loan shows the total
                        })
                    else:
                        loan_history.append({
                            "Month": m,
                            "Loan #": loan['loan_id'],
                            "BTC Price (USD)": price,
                            "Collateral Value (USD)": loan['btc_collateral'] * price,
                            "Loan Balance (USD)": loan['loan_balance'],
                            "Interest Accrued (Total)": loan['interest_accrued'],
                            "Monthly Payment": total_payment,
                            "LTV %": ltv_percent,
                            "At Risk of Liquidation": at_risk,
                            "Total Loan Balance (USD)": ""  # Empty for non-last loans
                        })

        # Remove rows where loan balance is 0 for all loans
        filtered_loan_history = [entry for entry in loan_history if entry['Loan Balance (USD)'] > 0]

        dca_df = pd.DataFrame(filtered_loan_history)
        st.subheader("DCA Independent Loan Snapshots")
        st.dataframe(dca_df.style.format({
            "BTC Price (USD)": "${:,.2f}",
            "Collateral Value (USD)": "${:,.2f}",
            "Loan Balance (USD)": "${:,.2f}",
            "Interest Accrued (Total)": "${:,.2f}",
            "Monthly Payment": "${:,.2f}",
            "LTV %": "{:.2f}%",
            "Total Loan Balance (USD)": "${:,.2f}"
        }), use_container_width=True)
