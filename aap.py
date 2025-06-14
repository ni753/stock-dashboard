import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pytz
import time
import requests
from io import StringIO

# Set Streamlit page layout
st.set_page_config(layout="wide")

# Auto-refresh every 60 seconds
rerun_interval = 60
if "rerun_time" not in st.session_state:
    st.session_state.rerun_time = time.time()

if time.time() - st.session_state.rerun_time > rerun_interval:
    st.session_state.rerun_time = time.time()
    st.experimental_rerun()

# Title
st.title("📈 Live Stock Analysis Dashboard")

# ✅ Load Nifty 500 list from GitHub using requests (avoids HTTPError)
try:
    url = "https://raw.githubusercontent.com/rohanrao619/nifty-indices-datasets/master/ind_nifty500list.csv"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    nifty_df = pd.read_csv(StringIO(response.text))
    nifty_df["Symbol_NS"] = nifty_df["Symbol"] + ".NS"
except Exception as e:
    st.error("⚠️ Could not fetch Nifty 500 list. Please try again later.")
    st.stop()

# Company dropdown
selected_company = st.selectbox("Select a Company", nifty_df["Company Name"].tolist())
selected_symbol = nifty_df[nifty_df["Company Name"] == selected_company]["Symbol_NS"].values[0]

# Fetch live stock data
data = yf.download(selected_symbol, period="1d", interval="5m")

# Handle no-data case
if data.empty or "Close" not in data.columns:
    st.error("❌ Live data not available at the moment. Please try again later or during market hours.")
else:
    # Convert time to IST
    data.index = data.index.tz_convert('Asia/Kolkata')
    data['Time'] = data.index.strftime('%H:%M:%S')

    # EMA calculations
    data['EMA_9'] = data['Close'].ewm(span=9, adjust=False).mean()
    data['EMA_15'] = data['Close'].ewm(span=15, adjust=False).mean()
    data['Signal'] = 0
    data.loc[data['EMA_9'] > data['EMA_15'], 'Signal'] = 1
    data.loc[data['EMA_9'] < data['EMA_15'], 'Signal'] = -1
    data['Crossover'] = data['Signal'].diff()

    # Show latest price
    try:
        latest_price = float(data['Close'].iloc[-1])
        latest_time = data.index[-1].strftime('%H:%M:%S')
        st.metric(label="Current Price", value=f"₹ {latest_price:.2f}", delta=f"As of {latest_time} IST")
    except:
        st.metric(label="Current Price", value="N/A", delta="Unavailable")

    # Plotting section
    st.subheader(f"{selected_symbol} - EMA Crossover Chart (Time in IST)")

    fig, ax = plt.subplots(figsize=(14, 6))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    ax.plot(data.index, data['Close'], label='Close', alpha=0.7, color='blue')
    ax.plot(data.index, data['EMA_9'], label='EMA 9', color='green')
    ax.plot(data.index, data['EMA_15'], label='EMA 15', color='red')

    # Crossover markers
    bullish = data[data['Crossover'] == 2]
    bearish = data[data['Crossover'] == -2]
    ax.scatter(bullish.index, bullish['Close'], marker='^', color='green', s=100, label='Bullish Crossover')
    ax.scatter(bearish.index, bearish['Close'], marker='v', color='red', s=100, label='Bearish Crossover')

    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M', tz=pytz.timezone("Asia/Kolkata")))
    fig.autofmt_xdate()

    # Clean styling
    ax.grid(False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('gray')
    ax.spines['left'].set_color('gray')

    ax.set_xlabel("Time (IST)")
    ax.set_ylabel("Price")
    ax.legend()

    st.pyplot(fig)
    plt.close(fig)
