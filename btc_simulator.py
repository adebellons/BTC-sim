import streamlit as st
import pandas as pd
import numpy as np

# Sample or actual data setup assumed
# dca_df = ...

# Ensure Date column is datetime
dca_df["Date"] = pd.to_datetime(dca_df["Date"])
dca_df["Month"] = dca_df["Date"].dt.to_period("M")

# Ensure numeric columns are numeric type
numeric_cols = [
    "BTC Price (USD)", "Collateral Value (USD)", "Loan Balance (USD)",
    "Interest Accrued (Total)", "Monthly Payment", "LTV %",
    "Total Loan Balance (USD)"
]
for col in numeric_cols:
    if col in dca_df.columns:
        dca_df[col] = pd.to_numeric(dca_df[col], errors="coerce")

# Compute total loan balance only for last row of each month
dca_df["Total Loan Balance (USD)"] = np.nan
for _, group in dca_df.groupby("Month"):
    if not group.empty:
        last_idx = group.index[-1]
        total = group["Loan Balance (USD)"].sum()
        dca_df.loc[last_idx, "Total Loan Balance (USD)"] = total

# Highlight only rows where total is shown
def highlight_total_row(row):
    if pd.notnull(row.get("Total Loan Balance (USD)", None)):
        return ["background-color: #ffe599"] * len(row)
    else:
        return [""] * len(row)

# Safe formatting for values that might be nan
def safe_money(x):
    return "" if pd.isna(x) else "${:,.2f}".format(x)

def safe_percent(x):
    return "" if pd.isna(x) else "{:.2f}%".format(x)

# Apply styling and formatting
styled_df = dca_df.style \
    .format({
        "BTC Price (USD)": safe_money,
        "Collateral Value (USD)": safe_money,
        "Loan Balance (USD)": safe_money,
        "Interest Accrued (Total)": safe_money,
        "Monthly Payment": safe_money,
        "LTV %": safe_percent,
        "Total Loan Balance (USD)": safe_money,
    }) \
    .apply(highlight_total_row, axis=1)

# Show the table
st.dataframe(styled_df)
