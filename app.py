import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pytz
import time

st.set_page_config(layout="wide")

# Auto-refresh every 60 seconds
rerun_interval = 60  # seconds

if "rerun_time" not in st.session_state:
    st.session_state.rerun_time = time.time()

if time.time() - st.session_state.rerun_time > rerun_interval:
    st.session_state.rerun_time = time.time()
    st.experimental_rerun()

# Page Title
st.title("📈 Live Stock Analysis Dashboard")

# Load Nifty 500 list
url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
nifty_df = pd.read_csv(url)
nifty_df["Symbol_NS"] = nifty_df["Symbol"] + ".NS"

# Dropdown to select company
selected_company = st.selectbox(
    "Select a Company",
    nifty_df["Company Name"].tolist()
)

# Get selected stock symbol
selected_symbol = nifty_df[nifty_df["Company Name"] == selected_company]["Symbol_NS"].values[0]

# Download stock data
data = yf.download(selected_symbol, period="1d", interval="5m")
data.dropna(inplace=True)

# Convert time to IST
data.index = data.index.tz_convert('Asia/Kolkata')

# Calculate EMA
data['EMA_9'] = data['Close'].ewm(span=9, adjust=False).mean()
data['EMA_15'] = data['Close'].ewm(span=15, adjust=False).mean()
data['Signal'] = 0
data.loc[data['EMA_9'] > data['EMA_15'], 'Signal'] = 1
data.loc[data['EMA_9'] < data['EMA_15'], 'Signal'] = -1
data['Crossover'] = data['Signal'].diff()

# Plot the chart
st.subheader(f"{selected_symbol} - EMA Crossover Chart")

fig, ax = plt.subplots(figsize=(14, 6))
fig.patch.set_facecolor('white')  # Plot background
ax.set_facecolor('white')         # Graph area background

ax.plot(data.index, data['Close'], label='Close', alpha=0.7, color='blue')
ax.plot(data.index, data['EMA_9'], label='EMA 9', color='green')
ax.plot(data.index, data['EMA_15'], label='EMA 15', color='red')

# Identify crossover points
bullish = data[data['Crossover'] == 2]
bearish = data[data['Crossover'] == -2]

# Highlight crossovers
ax.scatter(bullish.index, bullish['Close'], marker='^', color='green', s=100, label='Bullish Crossover')
ax.scatter(bearish.index, bearish['Close'], marker='v', color='red', s=100, label='Bearish Crossover')

# Format x-axis time to HH:MM IST
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
fig.autofmt_xdate()

# Remove grid rectangles
ax.grid(False)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_color('gray')
ax.spines['left'].set_color('gray')

# Axis labels and legend
ax.set_xlabel("Time (IST)")
ax.set_ylabel("Price")
ax.legend()

# Show plot
st.pyplot(fig)
plt.close(fig)
