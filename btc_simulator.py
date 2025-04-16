import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="BTC Loan Leverage Simulator", layout="wide")
st.title("BTC Loan Leverage Simulator")

# Sidebar inputs
st.sidebar.header("Simulation Inputs")
run_simulation = st.sidebar.button("Run Simulation")
initial_btc = st.sidebar.number_input("Initial BTC Amount", value=1.0, min_value=0.0)
use_historical_data = st.sidebar.checkbox("Use Historical Bitcoin Price Data for Prediction")
use_live_price       = st.sidebar.checkbox("Use Live Bitcoin Price")

if use_live_price:
    st.sidebar.write("Fetching live Bitcoin price...")
    try:
        live_price = yf.Ticker("BTC-USD").history(period="1d")['Close'].iloc[-1]
        st.sidebar.write(f"Live Bitcoin Price: ${live_price:,.2f}")
    except:
        st.sidebar.error("Error fetching live price")
else:
    live_price = None

initial_price = st.sidebar.number_input("Initial BTC Price (USD)", value=30000.0, min_value=0.0)
ltv         = st.sidebar.slider("Loan-to-Value (LTV %)", min_value=0, max_value=100, value=50)
liq_thresh  = st.sidebar.slider("Liquidation Threshold (%)", min_value=0, max_value=100, value=80)
interest_rt = st.sidebar.number_input("Loan Interest Rate (%)", value=5.0, min_value=0.0)
loan_term   = st.sidebar.number_input("Loan Term (months)", value=12, min_value=1)
monthly_dca = st.sidebar.number_input("Monthly DCA Amount (BTC)", value=0.01)
monthly_withdrawal = st.sidebar.number_input("Monthly Loan Withdrawal (USD)", value=500.0)
monthly_payment    = st.sidebar.number_input("Monthly Payment (USD)", value=0.0, min_value=0.0)

if run_simulation:
    # --- initialize ---
    btc_balance   = initial_btc
    loan_balance  = initial_btc * initial_price * (ltv / 100)
    monthly_int   = interest_rt / 12 / 100

    # build price forecast
    prices = []
    base_price = live_price if use_live_price and live_price else initial_price
    prices.append(base_price)
    if use_historical_data:
        hist = yf.download("BTC-USD", period="5y", interval="1mo")["Close"].pct_change().dropna()
        avg_pct = hist.mean()
        p=base_price
        for _ in range(loan_term):
            p *= (1 + avg_pct)
            prices.append(p)
    else:
        pct = st.sidebar.number_input("BTC Monthly Price Change (%)", value=2.0)
        p=base_price
        for _ in range(loan_term):
            p *= (1 + pct/100)
            prices.append(p)
    while len(prices) < loan_term+1:
        prices.append(prices[-1])

    # simulate
    data=[]
    total_int_accrued=0.0
    for m in range(loan_term+1):
        price = prices[m]
        btc_balance += monthly_dca
        btc_value = btc_balance*price

        if m>0:
            # interest on current balance
            mi = loan_balance * monthly_int
            total_int_accrued += mi
            # payment = max(interest, user payment)
            pay = max(mi, monthly_payment)
            pay = min(pay, loan_balance+mi+monthly_withdrawal)  # don't overpay
        else:
            mi=0; pay=0

        # update loan balance
        loan_balance = loan_balance + mi + monthly_withdrawal - pay
        loan_balance = max(loan_balance, 0)

        # liquidation check
        current_ltv = (loan_balance/btc_value*100) if btc_value>0 else 0
        risk = "Yes" if (current_ltv>liq_thresh and loan_balance>0) else "No"

        data.append({
            "Month": m,
            "BTC Price (USD)": price,
            "BTC Balance": btc_balance,
            "BTC Value (USD)": btc_value,
            "Loan Balance (USD)": loan_balance,
            "Interest Accrued (Total)": total_int_accrued,
            "Monthly Interest (USD)": mi,
            "Monthly Payment (USD)": pay,
            "LTV Current (%)": current_ltv,
            "Liquidation Risk": risk
        })

    df = pd.DataFrame(data)
    st.subheader("Simulation Results")
    st.dataframe(df.style.format({
        "BTC Price (USD)": "${:,.2f}",
        "BTC Value (USD)": "${:,.2f}",
        "Loan Balance (USD)": "${:,.2f}",
        "Interest Accrued (Total)": "${:,.2f}",
        "Monthly Interest (USD)": "${:,.2f}",
        "Monthly Payment (USD)": "${:,.2f}",
        "LTV Current (%)": "{:.2f}%"
    }))

    csv = df.to_csv(index=False).encode()
    st.download_button("Download CSV", csv, "btc_sim_results.csv", "text/csv")

else:
    st.info("Enter values and click Run Simulation")
