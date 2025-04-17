import streamlit as st
import pandas as pd
import numpy as np

# Sample data for demonstration (replace with your real dca_df)
# dca_df = your full dataframe with all necessary columns populated

# Calculate Total Loan Balance (USD) for last row of each month
dca_df["Month"] = pd.to_datetime(dca_df["Date"]).dt.to_period("M")
dca_df["Total Loan Balance (USD)"] = np.nan  # Start with NaNs

# Group by Month and set total loan value only for last row of each month
monthly_groups = dca_df.groupby("Month")
for _, group in monthly_groups:
    if not group.empty:
        last_idx = group.index[-1]
        total = group["Loan Balance (USD)"].sum()
        dca_df.loc[last_idx, "Total Loan Balance (USD)"] = total

# Convert safely so non-numerics become NaN
dca_df["Total Loan Balance (USD)"] = pd.to_numeric(dca_df["Total Loan Balance (USD)"], errors="coerce")

# Define styling function to highlight total row
def highlight_total_row(row):
    if pd.notnull(row["Total Loan Balance (USD)"]):
        return ["background-color: #ffe599"] * len(row)  # Light yellow
    else:
        return [""] * len(row)

# Format and style the DataFrame
styled_df = dca_df.style \
    .format({
        "BTC Price (USD)": "${:,.2f}",
        "Collateral Value (USD)": "${:,.2f}",
        "Loan Balance (USD)": "${:,.2f}",
        "Interest Accrued (Total)": "${:,.2f}",
        "Monthly Payment": "${:,.2f}",
        "LTV %": "{:.2f}%",
        "Total Loan Balance (USD)": "${:,.2f}"
    }) \
    .apply(highlight_total_row, axis=1)

# Display the styled dataframe in Streamlit
st.dataframe(styled_df)
