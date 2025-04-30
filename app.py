import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pytz
import time
from datetime import datetime, time as dtime

st.set_page_config(layout="wide", page_title="📈 Live Stock Analysis Dashboard", page_icon="📈")

# --- Auto-refresh every 5 minutes ---
rerun_interval = 300
if "rerun_time" not in st.session_state:
    st.session_state.rerun_time = time.time()

if time.time() - st.session_state.rerun_time > rerun_interval:
    st.session_state.rerun_time = time.time()
    st.experimental_rerun()

# --- Title ---
st.markdown("<h1 style='text-align: center; color: #2c3e50;'>📈 Live Stock Analysis Dashboard</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- Load Nifty 500 list ---
@st.cache_data
def load_nifty_500():
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    df = pd.read_csv(url)
    df["Symbol_NS"] = df["Symbol"] + ".NS"
    return df

nifty_df = load_nifty_500()

# --- Searchable Selectbox ---
selected_company = st.selectbox(
    "🔎 Search and Select a Company",
    nifty_df["Company Name"].tolist(),
    index=None,
    placeholder="Type to search...",
    key="company_search"
)

# --- Market open checker ---
def is_market_open():
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    market_start = dtime(9, 15)
    market_end = dtime(15, 30)
    return now.weekday() < 5 and market_start <= now.time() <= market_end

# --- Plotting Function ---
def plot_stock_chart(data, selected_symbol):
    data.index = data.index.tz_convert('Asia/Kolkata')
    data['Time'] = data.index.strftime('%H:%M:%S')
    data['EMA_9'] = data['Close'].ewm(span=9, adjust=False).mean()
    data['EMA_15'] = data['Close'].ewm(span=15, adjust=False).mean()
    data['Signal'] = 0
    data.loc[data['EMA_9'] > data['EMA_15'], 'Signal'] = 1
    data.loc[data['EMA_9'] < data['EMA_15'], 'Signal'] = -1
    data['Crossover'] = data['Signal'].diff()

    latest_price = float(data['Close'].iloc[-1])
    latest_time = data.index[-1].strftime('%H:%M:%S')
    st.metric(label=f"📊 {selected_company} Current Price", value=f"₹ {latest_price:.2f}", delta=f"As of {latest_time} IST")

    st.subheader(f"{selected_symbol} - EMA Crossover Chart with Buy/Sell Signals (IST Time)")

    fig, ax = plt.subplots(figsize=(14, 6))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    ax.plot(data.index, data['Close'], label='Close', alpha=0.7, color='blue')
    ax.plot(data.index, data['EMA_9'], label='EMA 9', color='green')
    ax.plot(data.index, data['EMA_15'], label='EMA 15', color='red')

    buy_signals = data[data['Crossover'] == 2]
    sell_signals = data[data['Crossover'] == -2]

    ax.scatter(buy_signals.index, buy_signals['Close'], marker='^', color='green', s=150, label='Buy Signal')
    for idx, row in buy_signals.iterrows():
        ax.annotate('🟢 BUY', (idx, row['Close']), textcoords="offset points", xytext=(0,10), ha='center', fontsize=8, color='green')

    ax.scatter(sell_signals.index, sell_signals['Close'], marker='v', color='red', s=150, label='Sell Signal')
    for idx, row in sell_signals.iterrows():
        ax.annotate('🔴 SELL', (idx, row['Close']), textcoords="offset points", xytext=(0,-15), ha='center', fontsize=8, color='red')

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M', tz=pytz.timezone("Asia/Kolkata")))
    fig.autofmt_xdate()

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

# --- Data Fetch & Display ---
if selected_company:
    selected_symbol = nifty_df[nifty_df["Company Name"] == selected_company]["Symbol_NS"].values[0]
    try:
        period = "1d" if is_market_open() else "2d"
        data = yf.download(selected_symbol, period=period, interval="5m")
        if data.empty or "Close" not in data.columns:
            raise ValueError("No valid data")

        # If market is closed, filter only the last full day
        if not is_market_open():
            last_day = data.index[-1].date()
            data = data[data.index.date == last_day]

        # Plot the chart
        plot_stock_chart(data, selected_symbol)

    except Exception:
        st.warning("⚠️ Unable to fetch data at the moment. Please try again later.")
else:
    st.info("🔔 Please search and select a company to view its analysis.")
