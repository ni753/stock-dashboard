import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pytz
import time
from datetime import datetime

st.set_page_config(layout="wide")
st.title("📈 Live Stock Analysis Dashboard")

# Auto-refresh every 60 seconds
rerun_interval = 60
if "rerun_time" not in st.session_state:
    st.session_state.rerun_time = time.time()

if time.time() - st.session_state.rerun_time > rerun_interval:
    st.session_state.rerun_time = time.time()
    st.experimental_rerun()

# Load Nifty 500
url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
nifty_df = pd.read_csv(url)
nifty_df["Symbol_NS"] = nifty_df["Symbol"] + ".NS"

# Select company
selected_company = st.selectbox("Select a Company", nifty_df["Company Name"].tolist())
selected_symbol = nifty_df[nifty_df["Company Name"] == selected_company]["Symbol_NS"].values[0]

# Function to fetch data
def fetch_data(symbol):
    data = yf.download(symbol, period="1d", interval="5m", progress=False)
    if data.empty or "Close" not in data.columns:
        data = yf.download(symbol, period="2d", interval="5m", progress=False)
        if not data.empty:
            data = data.iloc[:len(data) // 2 * -1]  # Use only previous day's data
            return data, False
        return pd.DataFrame(), None
    return data, True

data, is_today = fetch_data(selected_symbol)

# Handle data result
if data.empty:
    st.error("⚠️ Unable to fetch any data. Please check again later or during market hours.")
else:
    # Timezone conversion
    data.index = data.index.tz_convert('Asia/Kolkata')
    data['Time'] = data.index.strftime('%H:%M:%S')

    # EMA & Signals
    data['EMA_9'] = data['Close'].ewm(span=9).mean()
    data['EMA_15'] = data['Close'].ewm(span=15).mean()
    data['Signal'] = 0
    data.loc[data['EMA_9'] > data['EMA_15'], 'Signal'] = 1
    data.loc[data['EMA_9'] < data['EMA_15'], 'Signal'] = -1
    data['Crossover'] = data['Signal'].diff()

    # Price metric
    latest_price = data['Close'].iloc[-1]
    latest_time = data.index[-1].strftime('%H:%M:%S')
    price_label = "📊 Current Price (Live)" if is_today else "📊 Last Closing Price (Previous Day)"
    st.metric(label=price_label, value=f"₹ {latest_price:.2f}", delta=f"As of {latest_time} IST")

    # Chart
    st.subheader(f"{selected_symbol} - EMA Crossover Chart (Time in IST)")

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(data.index, data['Close'], label='Close', color='blue')
    ax.plot(data.index, data['EMA_9'], label='EMA 9', color='green')
    ax.plot(data.index, data['EMA_15'], label='EMA 15', color='red')

    buy = data[data['Crossover'] == 2]
    sell = data[data['Crossover'] == -2]
    ax.scatter(buy.index, buy['Close'], marker='^', color='green', s=100, label='Buy Signal')
    ax.scatter(sell.index, sell['Close'], marker='v', color='red', s=100, label='Sell Signal')

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M', tz=pytz.timezone('Asia/Kolkata')))
    fig.autofmt_xdate()

    ax.set_xlabel("Time (IST)")
    ax.set_ylabel("Price")
    ax.legend()
    ax.grid(False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    st.pyplot(fig)
    plt.close(fig)

    if not is_today:
        st.info("🕒 Market is currently closed. Displaying data from the previous trading day.")
