import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pytz
import time
from datetime import datetime, time as dtime

st.set_page_config(layout="wide", page_title="📈 Live Stock Analysis Dashboard", page_icon="📈")

# Auto-refresh every 5 minutes
rerun_interval = 300
if "rerun_time" not in st.session_state:
    st.session_state.rerun_time = time.time()

if time.time() - st.session_state.rerun_time > rerun_interval:
    st.session_state.rerun_time = time.time()
    st.experimental_rerun()

# Title
st.markdown("<h1 style='text-align: center;'>📈 Live Stock Analysis Dashboard</h1>", unsafe_allow_html=True)
st.markdown("---")

# Load Nifty 500 list
@st.cache_data
def load_nifty_500():
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    df = pd.read_csv(url)
    df["Symbol_NS"] = df["Symbol"] + ".NS"
    return df

nifty_df = load_nifty_500()

# Searchable Selectbox
selected_company = st.selectbox(
    "🔎 Search and Select a Company",
    nifty_df["Company Name"].tolist(),
    index=None,
    placeholder="Type to search...",
)

# Helper to check if market open
def is_market_open():
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    market_start = dtime(9, 15)
    market_end = dtime(15, 30)
    return now.weekday() < 5 and market_start <= now.time() <= market_end

if selected_company:
    selected_symbol = nifty_df[nifty_df["Company Name"] == selected_company]["Symbol_NS"].values[0]

    # Fetch intraday data
    period = "1d" if is_market_open() else "2d"

    data = yf.download(selected_symbol, period=period, interval="5m")
    
    if not is_market_open() and not data.empty:
        last_day = data.index[-1].date()
        data = data[data.index.date == last_day]

    if data.empty:
        st.error("❌ Data not available.")
    else:
        data.index = data.index.tz_convert('Asia/Kolkata')

        # Calculate EMAs
        data['EMA_9'] = data['Close'].ewm(span=9).mean()
        data['EMA_15'] = data['Close'].ewm(span=15).mean()

        # Generate signals
        data['Signal'] = 0
        data.loc[data['EMA_9'] > data['EMA_15'], 'Signal'] = 1
        data.loc[data['EMA_9'] < data['EMA_15'], 'Signal'] = -1
        data['Crossover'] = data['Signal'].diff()

        # Current price metric
        st.metric(f"📊 {selected_company} Current Price", f"₹ {data['Close'].iloc[-1]:.2f}")

        # Plot chart
        st.subheader(f"{selected_symbol} - EMA Crossover Chart")

        fig, ax = plt.subplots(figsize=(14, 6))

        ax.plot(data.index, data['Close'], label='Close', color='blue')
        ax.plot(data.index, data['EMA_9'], label='EMA 9', color='green')
        ax.plot(data.index, data['EMA_15'], label='EMA 15', color='red')

        # Buy/Sell markers
        buy_signals = data[data['Crossover'] == 2]
        sell_signals = data[data['Crossover'] == -2]

        ax.scatter(buy_signals.index, buy_signals['Close'], marker='^', color='green', s=100)
        ax.scatter(sell_signals.index, sell_signals['Close'], marker='v', color='red', s=100)

        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M', tz=pytz.timezone("Asia/Kolkata")))
        ax.legend()
        st.pyplot(fig)

else:
    st.info("🔔 Please search and select a company.")
