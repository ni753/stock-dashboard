import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pytz
import time

st.set_page_config(layout="wide", page_title="📈 Live Stock Analysis Dashboard", page_icon="📈")

# --- Auto-refresh every 60 seconds ---
rerun_interval = 60
if "rerun_time" not in st.session_state:
    st.session_state.rerun_time = time.time()

if time.time() - st.session_state.rerun_time > rerun_interval:
    st.session_state.rerun_time = time.time()
    st.experimental_rerun()

# --- Title ---
st.markdown("<h1 style='text-align: center; color: #2c3e50;'>📈 Live Stock Analysis Dashboard</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- NIFTY 50 and BANK NIFTY live data ---
index_symbols = {
    "NIFTY 50": "^NSEI",
    "BANK NIFTY": "^NSEBANK"
}

index_data = {}
for name, symbol in index_symbols.items():
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="1d", interval="5m")
    if not hist.empty:
        latest_price = hist['Close'].iloc[-1]
        index_data[name] = latest_price
    else:
        index_data[name] = None

col1, col2 = st.columns(2)
with col1:
    if index_data["NIFTY 50"]:
        st.metric(label="🌟 NIFTY 50", value=f"{index_data['NIFTY 50']:.2f}")
    else:
        st.metric(label="🌟 NIFTY 50", value="N/A")

with col2:
    if index_data["BANK NIFTY"]:
        st.metric(label="🏦 BANK NIFTY", value=f"{index_data['BANK NIFTY']:.2f}")
    else:
        st.metric(label="🏦 BANK NIFTY", value="N/A")

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

if selected_company:
    selected_symbol = nifty_df[nifty_df["Company Name"] == selected_company]["Symbol_NS"].values[0]

    # --- Fetch stock data ---
    data = yf.download(selected_symbol, period="1d", interval="5m")

    if data.empty or "Close" not in data.columns:
        st.error("❌ Live data not available at the moment. Please try again later or during market hours.")
    else:
        # Convert index to IST timezone (Asia/Kolkata)
        data.index = data.index.tz_convert('Asia/Kolkata')
        data['Time'] = data.index.strftime('%H:%M:%S')

        # EMA Calculation
        data['EMA_9'] = data['Close'].ewm(span=9, adjust=False).mean()
        data['EMA_15'] = data['Close'].ewm(span=15, adjust=False).mean()

        # Signal Generation
        data['Signal'] = 0
        data.loc[data['EMA_9'] > data['EMA_15'], 'Signal'] = 1
        data.loc[data['EMA_9'] < data['EMA_15'], 'Signal'] = -1
        data['Crossover'] = data['Signal'].diff()

        # --- Live price metric ---
        try:
            latest_price = float(data['Close'].iloc[-1])
            latest_time = data.index[-1].strftime('%H:%M:%S')  # IST format
            st.metric(label=f"📊 {selected_company} Current Price", value=f"₹ {latest_price:.2f}", delta=f"As of {latest_time} IST")
        except:
            st.metric(label="📊 Current Price", value="N/A", delta="Unavailable")

        # --- EMA crossover chart with Buy/Sell labels ---
        st.subheader(f"{selected_symbol} - EMA Crossover Chart with Buy/Sell Signals (IST Time)")

        fig, ax = plt.subplots(figsize=(14, 6))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')

        ax.plot(data.index, data['Close'], label='Close', alpha=0.7, color='blue')
        ax.plot(data.index, data['EMA_9'], label='EMA 9', color='green')
        ax.plot(data.index, data['EMA_15'], label='EMA 15', color='red')

        # Mark Buy and Sell Signals
        buy_signals = data[data['Crossover'] == 2]
        sell_signals = data[data['Crossover'] == -2]

        # Plot buy signals
        ax.scatter(buy_signals.index, buy_signals['Close'], marker='^', color='green', s=150, label='Buy Signal')
        for idx, row in buy_signals.iterrows():
            ax.annotate('🟢 BUY', (idx, row['Close']), textcoords="offset points", xytext=(0,10), ha='center', fontsize=8, color='green')

        # Plot sell signals
        ax.scatter(sell_signals.index, sell_signals['Close'], marker='v', color='red', s=150, label='Sell Signal')
        for idx, row in sell_signals.iterrows():
            ax.annotate('🔴 SELL', (idx, row['Close']), textcoords="offset points", xytext=(0,-15), ha='center', fontsize=8, color='red')

        # X-axis formatting
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M', tz=pytz.timezone("Asia/Kolkata")))
        fig.autofmt_xdate()

        # Clean style
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

else:
    st.info("🔔 Please search and select a company to view its live analysis.")
