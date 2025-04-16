import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="BTC Loan Leverage Simulator", layout="wide")
st.title("BTC Loan Leverage Simulator")

# Sidebar inputs
st.sidebar.header("Simulation Inputs")
run_simulation       = st.sidebar.button("Run Simulation")
initial_btc          = st.sidebar.number_input("Initial BTC Amount", value=1.0, min_value=0.0)
use_historical_data  = st.sidebar.checkbox("Use Historical Bitcoin Price Data for Prediction")
use_live_price       = st.sidebar.checkbox("Use Live Bitcoin Price")
initial_price        = st.sidebar.number_input("Initial BTC Price (USD)", value=30000.0, min_value=0.0)
ltv                  = st.sidebar.slider("Loan-to-Value (LTV %)", min_value=0, max_value=100, value=50)
liq_threshold        = st.sidebar.slider("Liquidation Threshold (%)", min_value=0, max_value=100, value=80)
interest_rate        = st.sidebar.number_input("Loan Interest Rate (%)", value=5.0, min_value=0.0)
loan_term            = st.sidebar.number_input("Loan Term (months)", value=12, min_value=1)
monthly_dca          = st.sidebar.number_input("Monthly DCA Amount (BTC)", value=0.01)
monthly_withdrawal   = st.sidebar.number_input("Monthly Loan Withdrawal (USD)", value=500.0)
monthly_payment_input= st.sidebar.number_input("Monthly Payment (USD)", value=0.0, min_value=0.0)

# Fetch live price if selected
live_price = None
if use_live_price:
    st.sidebar.write("Fetching live Bitcoin price...")
    try:
        live_price = yf.Ticker("BTC-USD").history(period="1d")['Close'].iloc[-1]
        st.sidebar.write(f"Live Bitcoin Price: ${live_price:,.2f}")
    except:
        st.sidebar.error("Error fetching live price")

if run_simulation:
    # --- Setup ---
    btc_balance   = initial_btc
    price0        = live_price if use_live_price and live_price else initial_price
    loan_balance  = initial_btc * price0 * (ltv / 100)  # initial loan
    monthly_int   = interest_rate / 12 / 100

    # build price forecast
    prices=[price0]
    if use_historical_data:
        hist = yf.download("BTC-USD", period="5y", interval="1mo")["Close"].pct_change().dropna()
        avg_pct = hist.mean()
        p=price0
        for _ in range(loan_term):
            p*= (1+avg_pct)
            prices.append(p)
    else:
        pct = st.sidebar.number_input("BTC Monthly Price Change (%)", value=2.0)
        p=price0
        for _ in range(loan_term):
            p*= (1+pct/100)
            prices.append(p)
    # pad
    while len(prices)<loan_term+1:
        prices.append(prices[-1])

    # --- Simulation ---
    rows=[]
    total_interest=0.0

    for m in range(loan_term+1):
        price = prices[m]
        btc_balance += monthly_dca
        btc_value   = btc_balance * price

        if m==0:
            interest=0.0
            payment =0.0
        else:
            # interest on *current* balance
            interest = loan_balance * monthly_int
            total_interest+= interest
            payment  = max(interest, monthly_payment_input)
            # update loan balance
            loan_balance = loan_balance + interest + monthly_withdrawal - payment
            loan_balance = max(loan_balance, 0.0)

        # current LTV for liquidation
        curr_ltv = (loan_balance / btc_value * 100) if btc_value>0 else 0
        risk = "Yes" if (curr_ltv > liq_threshold and loan_balance>0) else "No"

        rows.append({
            "Month": m,
            "BTC Price (USD)": price,
            "BTC Balance": btc_balance,
            "BTC Value (USD)": btc_value,
            "Loan Balance (USD)": loan_balance,
            "Interest Accrued (Total)": total_interest,
            "Monthly Interest (USD)": interest,
            "Monthly Payment (USD)": payment,
            "Current LTV (%)": curr_ltv,
            "Liquidation Risk": risk
        })

    df = pd.DataFrame(rows)
    st.subheader("Simulation Results")
    st.dataframe(df.style.format({
        "BTC Price (USD)": "${:,.2f}",
        "BTC Value (USD)": "${:,.2f}",
        "Loan Balance (USD)": "${:,.2f}",
        "Interest Accrued (Total)": "${:,.2f}",
        "Monthly Interest (USD)": "${:,.2f}",
        "Monthly Payment (USD)": "${:,.2f}",
        "Current LTV (%)": "{:.2f}%"
    }))

    st.download_button("Download CSV", df.to_csv(index=False).encode(), "btc_sim_results.csv", "text/csv")
else:
    st.info("Enter inputs and click **Run Simulation**")
