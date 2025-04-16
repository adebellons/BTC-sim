import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import requests
import pandas as pd

st.set_page_config(page_title="BTC-Backed Loan Simulator", layout="wide")
st.title("🚀 Bitcoin Wealth Leverage Simulator")

# --- Sidebar Inputs ---
st.sidebar.header("Simulation Settings")

# BTC price model selection
btc_price_mode = st.sidebar.radio("BTC Price Model", ["Simulated", "Flat Growth", "Historical"], index=0)

# New BTC price simulation parameters
btc_annual_growth = st.sidebar.slider("Expected Annual BTC Growth (%)", min_value=-50, max_value=200, value=10) / 100
btc_volatility = st.sidebar.slider("BTC Price Volatility (%)", min_value=1, max_value=200, value=20) / 100

simulation_mode = st.radio(
    "Choose Simulation Mode",
    ["Standard Loan", "DCA as Independent Loans"],
    index=0,
    horizontal=True
)
starting_btc = st.sidebar.number_input("Initial BTC Balance", value=1.0, step=0.1)

use_live_price = st.sidebar.checkbox("Use Live BTC Price", value=False)

if use_live_price:
    starting_price = 30000  # default fallback
    try:
        response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
        response.raise_for_status()
        starting_price = response.json()["bitcoin"]["usd"]
        st.sidebar.write(f"📈 Live BTC Price: ${starting_price:,.2f}")
    except Exception as e:
        st.sidebar.error("⚠️ Failed to fetch live BTC price. Using default.")
else:
    starting_price = st.sidebar.number_input("Initial BTC Price (USD)", value=30000, step=1000)

ltv_ratio = st.sidebar.slider("Loan-to-Value Ratio (%)", min_value=10, max_value=90, value=50) / 100
liquidation_ltv = st.sidebar.slider("Liquidation LTV Threshold (%)", min_value=50, max_value=100, value=85)
loan_interest_rate = st.sidebar.slider("Loan Interest Rate (Annual %)", min_value=1.00, max_value=15.00, value=6.00, step=0.01) / 100
monthly_dca_usd = st.sidebar.number_input("Monthly DCA Amount (USD)", value=500, step=50)
monthly_income_draw = st.sidebar.number_input("Monthly Income Withdrawal (USD)", value=1000, step=100)
minimum_monthly_payment = st.sidebar.number_input("Minimum Monthly Payment (USD)", value=0, step=50)
simulation_months = st.sidebar.slider("Simulation Length (Months)", 12, 60, 36)

# Library versions for debugging
with st.sidebar.expander("📦 Library Versions"):
    st.write(f"Streamlit: {st.__version__}")
    st.write(f"Pandas: {pd.__version__}")

# Simulate BTC price using a geometric growth model
def simulate_btc_price(months, start_price, annual_growth=0.1, volatility=0.2):
    monthly_growth = (1 + annual_growth) ** (1/12) - 1
    prices = [start_price]
    for _ in range(1, months):
        shock = np.random.normal(loc=monthly_growth, scale=volatility / np.sqrt(12))
        prices.append(prices[-1] * (1 + shock))
    return prices

if btc_price_mode == "Simulated":
    btc_prices = simulate_btc_price(simulation_months, starting_price, annual_growth=btc_annual_growth, volatility=btc_volatility)
elif btc_price_mode == "Flat Growth":
    monthly_growth = (1 + btc_annual_growth) ** (1/12) - 1
    btc_prices = [starting_price * (1 + monthly_growth) ** i for i in range(simulation_months)]
else:
    try:
        days_needed = simulation_months * 30
        url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days={days_needed}&interval=daily"
        response = requests.get(url)
        response.raise_for_status()
        prices_raw = response.json()["prices"]
        daily_prices = [price[1] for price in prices_raw]
        btc_prices = [daily_prices[i * 30] for i in range(simulation_months)]
    except Exception:
        st.sidebar.error("⚠️ Failed to fetch historical data. Using flat BTC price as fallback.")
        btc_prices = [starting_price for _ in range(simulation_months)]

# --- Simulation Logic ---
btc_holdings = starting_btc
loan_balance = starting_price * starting_btc * ltv_ratio
btc_collateral_value = []
loan_balances = []
available_equity = []
loan_opened_months = []
loan_age_months = []
overall_months = []

independent_loans = []
loan_data = []

for month in range(simulation_months):
    price = btc_prices[month]
    btc_dca = monthly_dca_usd / price
    btc_holdings += btc_dca

    if simulation_mode == "Standard Loan":
        loan_balance *= (1 + loan_interest_rate / 12)
        loan_balance += monthly_income_draw
        min_payment = max(loan_balance * (loan_interest_rate / 12), minimum_monthly_payment)
        loan_balance -= min_payment

    loan_opened_months.append(1)
    loan_age_months.append(month + 1)

    else:
        new_loan = btc_dca * price * ltv_ratio
        independent_loans.append({
            "start_month": month + 1,
            "amount": new_loan,
            "balance": new_loan,
            "age": 1
        })
        for loan in independent_loans:
            if loan["start_month"] < (month + 1):
                loan["age"] += 1
            loan["balance"] *= (1 + loan_interest_rate / 12)
            min_payment = max(loan["balance"] * (loan_interest_rate / 12), minimum_monthly_payment)
            loan["balance"] -= min_payment
        loan_balance = sum(loan["balance"] for loan in independent_loans) + monthly_income_draw

        for loan in independent_loans:
            min_payment = max(loan["balance"] * (loan_interest_rate / 12), minimum_monthly_payment)
            loan_data.append({
                "Loan # (Opened in Month)": loan["start_month"],
                "Month of This Loan": loan["age"],
                "Overall Month": month + 1,
                "BTC Price Now": f"{price:,.2f}",
                "BTC Collateral": f"{btc_holdings:.6f}",
                "Loan Principal": f"{loan['amount']:,.2f}",
                "Interest Accrued (Simple)": f"{loan['balance'] - loan['amount']:,.2f}",
                "Monthly Interest": f"{(loan_interest_rate / 12) * 100:.2f}",
                "Total Owed": f"{loan['balance']:,.2f}",
                "Minimum Payment": f"{min_payment:,.2f}",
                "LTV (%)": f"{(loan['balance'] / (btc_holdings * price)) * 100:.2f}",
                "Liquidation Risk": "Yes" if (loan['balance'] / (btc_holdings * price)) * 100 >= liquidation_ltv else "No"
            })

    total_collateral_value = btc_holdings * price
    equity = total_collateral_value - loan_balance

    btc_collateral_value.append(total_collateral_value)
    loan_balances.append(loan_balance)
    available_equity.append(equity)
    overall_months.append(month + 1)

btc_holdings_over_time = [starting_btc + sum(monthly_dca_usd / btc_prices[i] for i in range(m+1)) for m in range(simulation_months)]
loan_principal = starting_price * starting_btc * ltv_ratio
interest_accrued = [loan_balances[i] - (loan_principal + (monthly_income_draw * (i+1))) for i in range(simulation_months)]
ltv_percentages = [(loan_balances[i] / btc_collateral_value[i]) * 100 if btc_collateral_value[i] > 0 else 0 for i in range(simulation_months)]
liquidation_risks = ["Yes" if ltv_percentages[i] >= liquidation_ltv else "No" for i in range(simulation_months)]

# Main Summary Table
if simulation_mode == "Standard Loan":
    data = pd.DataFrame({
        'Overall Month': overall_months,
        'BTC Price Now': [f"{p:,.2f}" for p in btc_prices],
        'BTC Collateral': [f"{h:.6f}" for h in btc_holdings_over_time],
        'Loan Principal': [f"{loan_principal:,.2f}" for _ in range(simulation_months)],
        'Interest Accrued (Simple)': [f"{ia:,.2f}" for ia in interest_accrued],
        'Monthly Interest': [f"{(loan_interest_rate / 12) * 100:.2f}" for _ in range(simulation_months)],
        'Total Owed': [f"{v:,.2f}" for v in loan_balances],
        'Minimum Payment': [f"{max((v * loan_interest_rate / 12), minimum_monthly_payment):,.2f}" for v in loan_balances],
        'LTV (%)': [f"{ltv:.2f}" for ltv in ltv_percentages],
        'Liquidation Risk': liquidation_risks
    })
else:
    data = pd.DataFrame(loan_data)
    data["Overall Month"] = data["Overall Month"].astype(int)
    data = data.sort_values(by="Overall Month").reset_index(drop=True)

st.subheader("🗅️ Monthly Breakdown")
st.dataframe(data, use_container_width=True)

# --- BTC Price Chart ---
fig2, ax2 = plt.subplots(figsize=(12, 4))
ax2.plot(np.arange(simulation_months), btc_prices, label='BTC Price', color='orange')
ax2.set_title('Simulated BTC Price Over Time')
ax2.set_xlabel('Months')
ax2.set_ylabel('Price (USD)')
ax2.grid(True)
st.pyplot(fig2)

# --- Key Metrics ---
st.subheader("📊 Final Metrics")
st.metric("Final BTC Price", f"${btc_prices[-1]:,.2f}")
st.metric("Total BTC Holdings", f"{btc_holdings:.4f} BTC")
st.metric("Loan Balance", f"${loan_balance:,.2f}")
st.metric("Collateral Value", f"${btc_holdings * btc_prices[-1]:,.2f}")
st.metric("Equity", f"${btc_holdings * btc_prices[-1] - loan_balance:,.2f}")
