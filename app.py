import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pytz
import time

st.set_page_config(layout="wide")

# Auto-refresh every 60 seconds
rerun_interval = 60

if "rerun_time" not in st.session_state:
    st.session_state.rerun_time = time.time()

if time.time() - st.session_state.rerun_time > rerun_interval:
    st.session_state.rerun_time = time.time()
    st.experimental_rerun()

# Title
st.title("📈 Live Stock Analysis Dashboard with Time-Based Price Tracking")

# Load Nifty 500 list
url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
nifty_df = pd.read_csv(url)
nifty_df["Symbol_NS"] = nifty_df["Symbol"] + ".NS"

# Select box
selected_company = st.selectbox("Select a Company", nifty_df["Company Name"].tolist())
selected_symbol = nifty_df[nifty_df["Company Name"] == selected_company]["Symbol_NS"].values[0]

# Fetch live intraday stock data
data = yf.download(selected_symbol, period="1d", interval="5m")
data.dropna(inplace=True)

# Convert timestamps to Indian time
data.index = data.index.tz_convert('Asia/Kolkata')

# Time column for display/debugging
data['Time'] = data.index.strftime('%H:%M:%S')

# Calculate EMAs
data['EMA_9'] = data['Close'].ewm(span=9, adjust=False).mean()
data['EMA_15'] = data['Close'].ewm(span=15, adjust=False).mean()
data['Signal'] = 0
data.loc[data['EMA_9'] > data['EMA_15'], 'Signal'] = 1
data.loc[data['EMA_9'] < data['EMA_15'], 'Signal'] = -1
data['Crossover'] = data['Signal'].diff()

# Show latest price and time
latest_price = data['Close'][-1]
latest_time = data['Time'][-1]
st.metric(label="Current Price", value=f"₹ {latest_price:.2f}", delta=f"As of {latest_time}")

# Plot
st.subheader(f"{selected_symbol} - EMA Crossover Chart")

fig, ax = plt.subplots(figsize=(14, 6))
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

ax.plot(data.index, data['Close'], label='Close', alpha=0.7, color='blue')
ax.plot(data.index, data['EMA_9'], label='EMA 9', color='green')
ax.plot(data.index, data['EMA_15'], label='EMA 15', color='red')

bullish = data[data['Crossover'] == 2]
bearish = data[data['Crossover'] == -2]

ax.scatter(bullish.index, bullish['Close'], marker='^', color='green', s=100, label='Bullish Crossover')
ax.scatter(bearish.index, bearish['Close'], marker='v', color='red', s=100, label='Bearish Crossover')

# X-axis time formatting
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
fig.autofmt_xdate()

# Styling
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
