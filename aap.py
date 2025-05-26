import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pytz
import time

# --- Streamlit Page Config ---
st.set_page_config(layout="wide")

# --- Auto-refresh every 60 seconds ---
rerun_interval = 60
if "rerun_time" not in st.session_state:
    st.session_state.rerun_time = time.time()

if time.time() - st.session_state.rerun_time > rerun_interval:
    st.session_state.rerun_time = time.time()
    st.experimental_rerun()

# --- INDEX TICKERS for Marquee ---
index_tickers = {
    "NIFTY 50": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "SENSEX": "^BSESN",
    "BANKEX": "BSE-BANK.BO",
    "FINNIFTY": "^CNXFIN"
}

@st.cache_data(ttl=60)
def fetch_index_data():
    index_data = []
    for name, symbol in index_tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.history(period="1d")
            current = info['Close'].iloc[-1]
            prev = info['Close'].iloc[0]
            change = ((current - prev) / prev) * 100
            index_data.append(f"{name}: {current:.2f} ({change:+.2f}%)")
        except:
            index_data.append(f"{name}: N/A")
    return " | ".join(index_data)

# --- MARQUEE HEADER ---
marquee_text = fetch_index_data()
st.markdown(
    f"""
    <marquee behavior="scroll" direction="left" scrollamount="6"
        style="background-color:#e0f7fa; color:#0d47a1; padding: 10px; font-size:18px;
               font-weight: bold; border-radius: 8px; box-shadow: 0px 0px 6px rgba(0,0,0,0.2);">
        {marquee_text}
    </marquee>
    """,
    unsafe_allow_html=True
)

# --- Title Section ---
st.markdown("<h1 style='text-align: center; color: #004080;'>\ud83d\udcc8 Live Stock Analysis Dashboard</h1>", unsafe_allow_html=True)

# --- Company Dropdown ---
# Use local CSV instead of online fetch to avoid HTTPError
nifty_df = pd.read_csv("ind_nifty500list.csv")  # Make sure this file exists in your project directory
nifty_df["Symbol_NS"] = nifty_df["Symbol"] + ".NS"

st.markdown("<h4 style='color:#006699;'>\ud83d\udd0d Select a Company</h4>", unsafe_allow_html=True)
selected_company = st.selectbox("", nifty_df["Company Name"].tolist())
selected_symbol = nifty_df[nifty_df["Company Name"] == selected_company]["Symbol_NS"].values[0]

# --- Fetch Stock Data ---
data = yf.download(selected_symbol, period="1d", interval="5m")

if data.empty or "Close" not in data.columns:
    st.error("\u274c Live data not available at the moment. Please try again later or during market hours.")
else:
    # Timezone Conversion
    if data.index.tz is None:
        data.index = data.index.tz_localize('UTC').tz_convert('Asia/Kolkata')
    else:
        data.index = data.index.tz_convert('Asia/Kolkata')
    data['Time'] = data.index.strftime('%H:%M:%S')

    # EMA Calculations
    data['EMA_9'] = data['Close'].ewm(span=9, adjust=False).mean()
    data['EMA_15'] = data['Close'].ewm(span=15, adjust=False).mean()
    data['Signal'] = 0
    data.loc[data['EMA_9'] > data['EMA_15'], 'Signal'] = 1
    data.loc[data['EMA_9'] < data['EMA_15'], 'Signal'] = -1
    data['Crossover'] = data['Signal'].diff()

    # --- Show Current Price Metric ---
    latest_price = float(data['Close'].iloc[-1])
    latest_time = data.index[-1].strftime('%H:%M:%S')

    col1, col2 = st.columns([2, 1])
    with col1:
        st.metric(label="\ud83d\udcb9 Current Price", value=f"\u20b9 {latest_price:.2f}", delta=f"As of {latest_time} IST")

    # --- EMA Crossover Chart ---
    st.markdown(f"<h3 style='color:#1a237e;'>\ud83d\udcca {selected_symbol} - EMA Crossover Chart (Time in IST)</h3>", unsafe_allow_html=True)

    fig, ax = plt.subplots(figsize=(14, 6))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    ax.plot(data.index, data['Close'], label='Close', alpha=0.7, color='blue')
    ax.plot(data.index, data['EMA_9'], label='EMA 9', color='green')
    ax.plot(data.index, data['EMA_15'], label='EMA 15', color='red')

    # Crossovers
    bullish = data[data['Crossover'] == 2]
    bearish = data[data['Crossover'] == -2]
    ax.scatter(bullish.index, bullish['Close'], marker='^', color='green', s=100, label='Bullish Crossover')
    ax.scatter(bearish.index, bearish['Close'], marker='v', color='red', s=100, label='Bearish Crossover')

    # X-axis format
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M', tz=pytz.timezone("Asia/Kolkata")))
    fig.autofmt_xdate()

    # Chart Style
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
