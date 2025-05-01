import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import time
from datetime import datetime

# Nifty 500 List
url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
nifty_df = pd.read_csv(url)
nifty_df["Symbol_NS"] = nifty_df["Symbol"] + ".NS"

# Sidebar Company Select
st.sidebar.title("Select Stock")
company = st.sidebar.selectbox("Company", nifty_df["Company Name"])
selected_symbol = nifty_df[nifty_df["Company Name"] == company]["Symbol_NS"].values[0]

# Main Title
st.title(f"{company} - Live EMA Crossover")

# Container for chart
plot_area = st.empty()

def is_market_open():
    now = datetime.now()
    # Market opens at 9:15 AM and closes at 3:30 PM (Indian Time)
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return market_open <= now <= market_close

# Function to fetch data from Yahoo Finance
def fetch_data(symbol):
    try:
        data = yf.download(symbol, period="1d", interval="5m")
        if data.empty:
            st.warning("No data available. Please try again later.")
            return None
        return data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

while True:
    # Only fetch data if market is open
    if is_market_open():
        data = fetch_data(selected_symbol)
        
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

            # Display plot
            plot_area.pyplot(fig)
        else:
            st.warning("No data available for the selected stock.")
    else:
        st.warning("The market is closed. Please check back during market hours.")

    time.sleep(60)  # Refresh every 60 seconds
