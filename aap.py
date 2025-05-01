import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import time

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

while True:
    data = yf.download(selected_symbol, period="1d", interval="5m")
    data['EMA_9'] = data['Close'].ewm(span=9, adjust=False).mean()
    data['EMA_15'] = data['Close'].ewm(span=15, adjust=False).mean()
    data['Signal'] = 0
    data.loc[data['EMA_9'] > data['EMA_15'], 'Signal'] = 1
    data.loc[data['EMA_9'] < data['EMA_15'], 'Signal'] = -1
    data['Crossover'] = data['Signal'].diff()

    # Plot
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

    time.sleep(60)  # Refresh every 60 seconds
