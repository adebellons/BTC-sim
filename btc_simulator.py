import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Simulate the DCA loan chart
def simulate_dca_loan_chart(
    btc_prices,
    dca_amount_usd,
    ltv,
    interest_rate,
    monthly_payment_pct
):
    # Example logic for generating DCA loan chart (replace with actual simulation)
    data = {
        "Date": pd.date_range(start="2023-01-01", periods=12, freq="M"),
        "Collateral Value (USD)": np.random.rand(12) * 10000,  # Random data for example
        "Loan Balance (USD)": np.random.rand(12) * 5000,  # Random data for example
        "Interest Accrued (Total)": np.random.rand(12) * 100,  # Random data for example
        "Monthly Payment": np.random.rand(12) * 50,  # Random data for example
        "Total Loan Balance (USD)": np.random.rand(12) * 5000,  # Random data for example
        "BTC Price (USD)": np.random.rand(12) * 40000,  # Random data for example
        "LTV %": np.random.rand(12) * 100  # Random data for example
    }
    return pd.DataFrame(data)

# Assume this returns your DCA loan chart
btc_prices = np.random.rand(12) * 40000  # Replace with actual BTC prices or method to fetch them

dca_amount_usd = 500  # Example DCA amount
ltv = 0.5
interest_rate = 0.08
monthly_payment_pct = 0.01

dca_df = simulate_dca_loan_chart(
    btc_prices=btc_prices,
    dca_amount_usd=dca_amount_usd,
    ltv=ltv,
    interest_rate=interest_rate,
    monthly_payment_pct=monthly_payment_pct
)

# Ensure Date column is datetime
dca_df["Date"] = pd.to_datetime(dca_df["Date"])
dca_df["Month"] = dca_df["Date"].dt.to_period("M")

# Ensure numeric columns are numeric type
numeric_columns = [
    "Collateral Value (USD)", "Loan Balance (USD)", "Interest Accrued (Total)",
    "Monthly Payment", "Total Loan Balance (USD)", "BTC Price (USD)", "LTV %"
]
for col in numeric_columns:
    dca_df[col] = pd.to_numeric(dca_df[col], errors='coerce')

# Determine the last row for each month
dca_df["Is Month End"] = dca_df["Month"] != dca_df["Month"].shift(-1)

# Set all "Total Loan Balance (USD)" except last row of month to blank
dca_df["Total Loan Balance (USD) Display"] = dca_df.apply(
    lambda row: row["Total Loan Balance (USD)"] if row["Is Month End"] else "",
    axis=1
)

# Display
styled_df = dca_df.style.format({
    "BTC Price (USD)": "${:,.2f}",
    "Collateral Value (USD)": "${:,.2f}",
    "Loan Balance (USD)": "${:,.2f}",
    "Interest Accrued (Total)": "${:,.2f}",
    "Monthly Payment": "${:,.2f}",
    "LTV %": "{:.2f}%",
    "Total Loan Balance (USD) Display": "${:,.2f}"
})

st.dataframe(styled_df, use_container_width=True)
