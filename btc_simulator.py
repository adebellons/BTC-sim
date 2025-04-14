import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="BTC-Backed Loan Simulator", layout="wide")
st.title("🚀 Bitcoin Wealth Leverage Simulator")

# --- Sidebar Inputs ---
st.sidebar.header("Simulation Settings")
starting_btc = st.sidebar.number_input("Initial BTC Balance", value=1.0, step=0.1)
starting_price = st.sidebar.number_input("Initial BTC Price (USD)", value=30000, step=1000)
ltv_ratio = st.sidebar.slider("Loan-to-Value Ratio (%)", min_value=10, max_value=90, value=50) / 100
liquidation_ltv = st.sidebar.slider("Liquidation LTV Threshold (%)", min_value=50, max_value=100, value=85)
loan_interest_rate = st.sidebar.slider("Loan Interest Rate (Annual %)", min_value=1, max_value=15, value=6) / 100
monthly_dca_usd = st.sidebar.number_input("Monthly DCA Amount (USD)", value=500, step=50)
monthly_income_draw = st.sidebar.number_input("Monthly Income Withdrawal (USD)", value=1000, step=100)
simulation_years = st.sidebar.slider("Simulation Length (Years)", 1, 30, 10)
simulation_months = simulation_years * 12

# Simulate BTC price using a geometric growth model
def simulate_btc_price(months, start_price, annual_growth=0.1, volatility=0.2):
    monthly_growth = (1 + annual_growth) ** (1/12) - 1
    prices = [start_price]
    for _ in range(1, months):
        shock = np.random.normal(loc=monthly_growth, scale=volatility / np.sqrt(12))
        prices.append(prices[-1] * (1 + shock))
    return prices

btc_prices = simulate_btc_price(simulation_months, starting_price)

# --- Simulation Logic ---
btc_holdings = starting_btc
loan_balance = starting_price * starting_btc * ltv_ratio
btc_collateral_value = []
loan_balances = []
available_equity = []

for month in range(simulation_months):
    price = btc_prices[month]
    btc_dca = monthly_dca_usd / price
    btc_holdings += btc_dca
    loan_balance *= (1 + loan_interest_rate / 12)
    loan_balance += monthly_income_draw

    total_collateral_value = btc_holdings * price
    equity = total_collateral_value - loan_balance

    btc_collateral_value.append(total_collateral_value)
    loan_balances.append(loan_balance)
    available_equity.append(equity)

# --- Display Charts ---
months = np.arange(simulation_months)
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(months, btc_collateral_value, label='BTC Collateral Value')
ax.plot(months, loan_balances, label='Loan Balance')
ax.plot(months, available_equity, label='Equity')
ax.set_title('Bitcoin Wealth Leverage Over Time')
ax.set_xlabel('Months')
ax.set_ylabel('USD')
ax.legend()
ax.grid(True)
st.pyplot(fig)

# --- Key Metrics ---
st.subheader("📊 Final Metrics")
st.metric("Final BTC Price", f"${btc_prices[-1]:,.2f}")
st.metric("Total BTC Holdings", f"{btc_holdings:.4f} BTC")
st.metric("Loan Balance", f"${loan_balance:,.2f}")
st.metric("Collateral Value", f"${btc_holdings * btc_prices[-1]:,.2f}")
st.metric("Equity", f"${btc_holdings * btc_prices[-1] - loan_balance:,.2f}")
