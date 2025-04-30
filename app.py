# stock_dashboard.py

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time

# ========== Header ==========
st.set_page_config(page_title="Stock Technical Dashboard", layout="wide")
st.title("📈 Real-Time Stock Analysis with EMA Crossovers")

# ========== Stock List ==========
@st.cache_data
def get_nifty_500():
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    return pd.read_csv(url)["Symbol"].tolist()

stocks = get_nifty_500()
selected_stock = st.selectbox("Choose a Nifty 500 stock:", stocks)

# ========== Fetch Data ==========
def fetch_data(symbol):
    data = yf.download(tickers=symbol + ".NS", interval="5m", period="1d", progress=False)
    data.dropna(inplace=True)
    data['EMA9'] = data['Close'].ewm(span=9).mean()
    data['EMA15'] = data['Close'].ewm(span=15).mean()
    return data

data = fetch_data(selected_stock)

# ========== Signal Logic ==========
def generate_signals(data):
    data['Signal'] = 0
    data['Signal'][9:] = np.where(data['EMA9'][9:] > data['EMA15'][9:], 1, 0)
    data['Position'] = data['Signal'].diff()
    return data

data = generate_signals(data)

# ========== Plotting ==========
fig = go.Figure()
fig.add_trace(go.Candlestick(x=data.index,
                             open=data['Open'], high=data['High'],
                             low=data['Low'], close=data['Close'],
                             name="Price"))
fig.add_trace(go.Scatter(x=data.index, y=data['EMA9'], line=dict(color='blue', width=1), name='EMA 9'))
fig.add_trace(go.Scatter(x=data.index, y=data['EMA15'], line=dict(color='orange', width=1), name='EMA 15'))

# Buy/Sell markers
buy_signals = data[data['Position'] == 1]
sell_signals = data[data['Position'] == -1]

fig.add_trace(go.Scatter(x=buy_signals.index, y=buy_signals['Close'], mode='markers',
                         marker=dict(color='green', size=10), name='Buy Signal'))
fig.add_trace(go.Scatter(x=sell_signals.index, y=sell_signals['Close'], mode='markers',
                         marker=dict(color='red', size=10), name='Sell Signal'))

fig.update_layout(title=f"{selected_stock} Live EMA Crossover", xaxis_rangeslider_visible=False)

st.plotly_chart(fig, use_container_width=True)

# ========== Auto Refresh ==========
st.caption("Auto-refreshes every 60 seconds.")
time.sleep(60)
st.experimental_rerun()
