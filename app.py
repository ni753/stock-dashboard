import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pytz
import time

st.set_page_config(layout="wide")

# ========== Auto-refresh every 60s ==========
rerun_interval = 60
if "rerun_time" not in st.session_state:
    st.session_state.rerun_time = time.time()

if time.time() - st.session_state.rerun_time > rerun_interval:
    st.session_state.rerun_time = time.time()
    st.experimental_rerun()

# ========== INDEX TICKERS ==========
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

# ========== MARQUEE HEADER ==========
marquee_text = fetch_index_data()
st.markdown(
    f"""
    <marquee behavior="scroll" direction="left" scrollamount="5" style="background-color:#f8f9fa; color:#000000; padding: 8px; font-weight: bold; border-radius: 5px;">
        {marquee_text}
    </marquee>
    """,
    unsafe_allow_html=True
)

# ========== TITLE ==========
st.title("📈 Live Stock Analysis Dashboard")

# ========== Company Dropdown ==========
url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
nifty_df = pd.read_csv(url)
nifty_df["Symbol_NS"] = nifty_df["Symbol"] + ".NS"
selected_company = st.selectbox("Select a Company", nifty_df["Company Name"].tolist())
selected_symbol = nifty_df[nifty_df["Company Name"] == selected_company]["Symbol_NS"].values[0]

# ========== Fetch Stock Data ==========
data = yf.download(selected_symbol, period="1d", interval="5m")

if data.empty or "Close" not in data.columns:
    st.error("❌ Live data not available at the moment. Please try again later or during market hours.")
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

    # ========== Show Price ==========
    latest_price = float(data['Close'].iloc[-1])
    latest_time = data.index[-1].strftime('%H:%M:%S')
    st.metric(label="Current Price", value=f"₹ {latest_price:.2f}", delta=f"As of {latest_time} IST")

    # ========== EMA Chart ==========
    st.subheader(f"{selected_symbol} - EMA Crossover Chart (Time in IST)")
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

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M', tz=pytz.timezone("Asia/Kolkata")))
    fig.autofmt_xdate()

    # Style
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
