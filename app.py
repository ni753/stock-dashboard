import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import time

# Auto refresh every 60 seconds
st.experimental_rerun() if st.session_state.get("rerun_time", 0) < time.time() else None
st.session_state["rerun_time"] = time.time() + 60

st.set_page_config(layout="wide")
st.title("📈 Live Stock Analysis Dashboard with EMA Crossover")

# Load Nifty 500
url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
nifty_df = pd.read_csv(url)
nifty_df["Symbol_NS"] = nifty_df["Symbol"] + ".NS"

# Dropdown
selected_company = st.selectbox(
    "Select a Company",
    nifty_df["Company Name"].tolist()
)

selected_symbol = nifty_df[nifty_df["Company Name"] == selected_company]["Symbol_NS"].values[0]

# Load stock data
data = yf.download(selected_symbol, period="1d", interval="5m")
data.dropna(inplace=True)

# EMA calculation
data['EMA_9'] = data['Close'].ewm(span=9, adjust=False).mean()
data['EMA_15'] = data['Close'].ewm(span=15, adjust=False).mean()
data['Signal'] = 0
data.loc[data['EMA_9'] > data['EMA_15'], 'Signal'] = 1
data.loc[data['EMA_9'] < data['EMA_15'], 'Signal'] = -1
data['Crossover'] = data['Signal'].diff()

# Plot
st.subheader(f"{selected_symbol} - EMA Crossover Chart")

fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(data.index, data['Close'], label='Close', alpha=0.5, color='blue')
ax.plot(data.index, data['EMA_9'], label='EMA 9', color='green')
ax.plot(data.index, data['EMA_15'], label='EMA 15', color='red')

bullish = data[data['Crossover'] == 2]
bearish = data[data['Crossover'] == -2]

ax.scatter(bullish.index, bullish['Close'], marker='^', color='green', s=100, label='Bullish Crossover')
ax.scatter(bearish.index, bearish['Close'], marker='v', color='red', s=100, label='Bearish Crossover')

ax.set_xlabel("Time")
ax.set_ylabel("Price")
ax.legend()
ax.grid(True)

st.pyplot(fig)
