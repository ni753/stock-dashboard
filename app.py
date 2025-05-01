import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pytz
import time
import requests
from io import StringIO

st.set_page_config(layout="wide")

# Auto-refresh every 60 seconds
rerun_interval = 60
if "rerun_time" not in st.session_state:
    st.session_state.rerun_time = time.time()

if time.time() - st.session_state.rerun_time > rerun_interval:
    st.session_state.rerun_time = time.time()
    st.experimental_rerun()

# Title
st.title("📈 Live Stock Analysis Dashboard with EMA Crossover")

# Load Nifty 500 list with fallback
@st.cache_data
def load_nifty_500():
    try:
        url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return pd.read_csv(StringIO(response.text))
        else:
            st.warning("⚠️ Failed to fetch from NSE. Using local fallback.")
            return pd.read_csv("ind_nifty500list.csv")
    except:
        st.warning("⚠️ Could not load from internet. Using local fallback.")
        return pd.read_csv("ind_nifty500list.csv")

nifty_df = load_nifty_500()
nifty_df["Symbol_NS"] = nifty_df["Symbol"] + ".NS"

# Company dropdown
selected_company = st.selectbox("Select a Company", nifty_df["Company Name"].tolist())
selected_symbol = nifty_df[nifty_df["Company Name"] == selected_company]["Symbol_NS"].values[0]

# Fetch live data
data = yf.download(selected_symbol, period="1d", interval="5m")

if data.empty or "Close" not in data.columns:
    st.error("❌ Live data not available at the moment. Please try again later or during market hours.")
else:
    # Convert index to IST timezone
    data.index = data.index.tz_convert('Asia/Kolkata')
    data['Time'] = data.index.strftime('%H:%M:%S')

    # EMA Calculation
    data['EMA_9'] = data['Close'].ewm(span=9, adjust=False).mean()
    data['EMA_15'] = data['Close'].ewm(span=15, adjust=False).mean()
    data['Signal'] = 0
    data.loc[data['EMA_9'] > data['EMA_15'], 'Signal'] = 1
    data.loc[data['EMA_9'] < data['EMA_15'], 'Signal'] = -1
    data['Crossover'] = data['Signal'].diff()

    # Show live price
    try:
        latest_price = float(data['Close'].iloc[-1])
        latest_time = data.index[-1].strftime('%H:%M:%S')  # IST format
        st.metric(label="Current Price", value=f"₹ {latest_price:.2f}", delta=f"As of {latest_time} IST")
    except:
        st.metric(label="Current Price", value="N/A", delta="Unavailable")

    # Plotting
    st.subheader(f"{selected_symbol} - EMA Crossover Chart (Time in IST)")
    fig, ax = plt.subplots(figsize=(14, 6))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    ax.plot(data.index, data['Close'], label='Close', alpha=0.7, color='blue')
    ax.plot(data.index, data['EMA_9'], label='EMA 9', color='green')
    ax.plot(data.index, data['EMA_15'], label='EMA 15', color='red')

    # Crossover points
    bullish = data[data['Crossover'] == 1]
    bearish = data[data['Crossover'] == -1]

    ax.scatter(bullish.index, bullish['Close'], marker='^', color='green', s=100, label='Bullish Crossover')
    ax.scatter(bearish.index, bearish['Close'], marker='v', color='red', s=100, label='Bearish Crossover')

    # X-axis formatting
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M', tz=pytz.timezone("Asia/Kolkata")))
    fig.autofmt_xdate()

    # Clean look
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
