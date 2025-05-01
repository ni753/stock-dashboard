import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime

# Load Nifty 500 List
url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
nifty_df = pd.read_csv(url)
nifty_df["Symbol_NS"] = nifty_df["Symbol"] + ".NS"

# Sidebar
st.sidebar.title("Stock Settings")
company = st.sidebar.selectbox("Select Company", nifty_df["Company Name"])
selected_symbol = nifty_df[nifty_df["Company Name"] == company]["Symbol_NS"].values[0]

period = st.sidebar.selectbox("Select Period", ["1d", "5d", "1mo", "3mo", "6mo", "1y"])
interval = st.sidebar.selectbox("Interval", ["5m", "15m", "30m", "1h", "1d"])

st.title(f"{company} - EMA Crossover Analysis")

# Function to fetch data
@st.cache_data(ttl=300)  # Cache data for 5 minutes
def fetch_data(symbol, period, interval):
    data = yf.download(symbol, period=period, interval=interval)
    if data.empty:
        return None
    return data

data = fetch_data(selected_symbol, period, interval)

if data is not None:
    data['EMA_9'] = data['Close'].ewm(span=9, adjust=False).mean()
    data['EMA_15'] = data['Close'].ewm(span=15, adjust=False).mean()
    data['Signal'] = 0
    data.loc[data['EMA_9'] > data['EMA_15'], 'Signal'] = 1
    data.loc[data['EMA_9'] < data['EMA_15'], 'Signal'] = -1
    data['Crossover'] = data['Signal'].diff()

    # Plotting
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(data.index, data['Close'], label='Close', color='blue', alpha=0.5)
    ax.plot(data.index, data['EMA_9'], label='EMA 9', color='green')
    ax.plot(data.index, data['EMA_15'], label='EMA 15', color='red')

    bullish = data[data['Crossover'] == 2]
    bearish = data[data['Crossover'] == -2]
    ax.scatter(bullish.index, bullish['Close'], marker='^', color='green', label='Bullish', s=100)
    ax.scatter(bearish.index, bearish['Close'], marker='v', color='red', label='Bearish', s=100)

    ax.legend()
    ax.grid(True)
    ax.set_title(f"{company} - EMA Crossover Chart")

    st.pyplot(fig)
else:
    st.warning("No data available. Please try again later.")
