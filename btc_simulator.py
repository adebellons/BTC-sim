import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="BTC Sim", layout="wide")
st.title("BTC Sim")

# Sidebar inputs
st.sidebar.header("Simulation Inputs")
initial_btc = st.sidebar.number_input("Initial BTC Amount", value=1.0, min_value=0.0)
initial_price = st.sidebar.number_input("Initial BTC Price (USD)", value=30000.0, min_value=0.0)
ltv = st.sidebar.slider("Loan-to-Value (LTV %)", min_value=0, max_value=100, value=50)
interest_rate = st.sidebar.number_input("Loan Interest Rate (%)", value=5.0, min_value=0.0)
loan_term = st.sidebar.number_input("Loan Term (months)", value=12, min_value=1)
monthly_price_change = st.sidebar.number_input("BTC Monthly Price Change (%)", value=2.0)
monthly_dca = st.sidebar.number_input("Monthly DCA Amount (BTC)", value=0.01)
monthly_withdrawal = st.sidebar.number_input("Monthly Income Withdrawal (USD)", value=500.0)
monthly_payment = st.sidebar.number_input("Monthly Payment (USD)", value=0.0, min_value=0.0)  # New input

run_simulation = st.sidebar.button("Run Simulation")

if run_simulation:
    # Initial values
    btc_price = initial_price
    btc_balance = initial_btc
    loan_amount = initial_btc * initial_price * (ltv / 100)
    monthly_interest = interest_rate / 12 / 100

    # Tracking
    data = []
    liquidation_triggered = False
    liquidation_month = None
    total_interest_accrued = 0.0  # Track total interest accrued

    for month in range(loan_term + 1):
        total_btc_value = btc_balance * btc_price
        interest_accrued = loan_amount * monthly_interest  # Interest for the month
        total_interest_accrued += interest_accrued  # Add to total interest

        # Calculate minimum payment: minimum of interest or monthly payment
        minimum_payment = max(interest_accrued, monthly_payment)

        if not liquidation_triggered and total_btc_value < loan_amount:
            liquidation_triggered = True
            liquidation_month = month

        data.append({
            "Month": month,
            "BTC Price": btc_price,
            "BTC Balance": btc_balance,
            "BTC Value (USD)": total_btc_value,
            "Loan Balance (USD)": loan_amount,
            "Interest Accrued (USD)": total_interest_accrued,
            "Minimum Payment (USD)": minimum_payment,
            "Liquidation Risk": "⚠️" if total_btc_value < loan_amount else ""
        })

        # Simulate next month
        btc_price *= (1 + monthly_price_change / 100)
        btc_balance += monthly_dca
        loan_amount += monthly_withdrawal
        loan_amount += interest_accrued  # Add interest to loan balance

        # Apply the minimum payment to reduce the loan balance
        loan_amount -= minimum_payment

    df = pd.DataFrame(data)

    # Chart
    st.subheader("Simulation Chart")
    fig, ax = plt.subplots()
    ax.plot(df["Month"], df["BTC Value (USD)"], label="BTC Value", color='orange')
    ax.plot(df["Month"], df["Loan Balance (USD)"], label="Loan Balance", color='red')
    ax.plot(df["Month"], df["Interest Accrued (USD)"], label="Interest Accrued", color='blue')
    ax.set_xlabel("Month")
    ax.set_ylabel("USD")
    ax.set_title("BTC Value vs Loan vs Interest Accrued")
    ax.legend()
    st.pyplot(fig)

    # Liquidation warning
    if liquidation_triggered:
        st.warning(f"⚠️ Liquidation risk: BTC value drops below loan in **month {liquidation_month}**.")

    # Final summary
    st.subheader("Final Summary")
    st.write(df.tail(1))

    # Table
    with st.expander("📊 Full Simulation Data"):
        st.dataframe(df.style.format({
            "BTC Price": "${:,.2f}",
            "BTC Value (USD)": "${:,.2f}",
            "Loan Balance (USD)": "${:,.2f}",
            "Interest Accrued (USD)": "${:,.2f}",
            "Minimum Payment (USD)": "${:,.2f}"
        }))

    # CSV download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "btc_sim_results.csv", "text/csv")

else:
    st.info("Enter values on the left and click 'Run Simulation' to see the results.")
