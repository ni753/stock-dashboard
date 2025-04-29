import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pytz
import time
import requests
from streamlit_marquee import streamlit_marquee

st.set_page_config(layout="wide")

# Auto-refresh every 60 seconds
rerun_interval = 60
if "rerun_time" not in st.session_state:
    st.session_state.rerun_time = time.time()

if time.time() - st.session_state.rerun_time > rerun_interval:
    st.session_state.rerun_time = time.time()
    st.experimental_rerun()

# ---- Index Marquee Header ----
indices = {
    "NIFTY 50": "^NSEI",
    "BANK NIFTY": "^NSEBANK",
    "SENSEX": "^BSESN",
    "NIFTY IT": "^CNXIT",
    "NIFTY PHARMA": "^CNXPHARMA",
    "NIFTY AUTO": "^CNXAUTO"
}

index_texts = []
for name, symbol in indices.items():
    try:
        df = yf.download(symbol, period="1d", interval="1m")
        if not df.empty:
            last_price = df['Close'].iloc[-1]
            change = last_price - df['Close'].iloc[-2]
            percent_change = (change / df['Close'].iloc[-2]) * 100
            color = "green" if change >= 0 else "red"
            index_texts.append(f"<span style='color:{color}'><b>{name}: ₹{last_price:.2f} ({percent_change:+.2f}%)</b></span>")
    except:
        continue

header_marquee = "       ".join(index_texts)

st.markdown("""
    <div style='background-color:#f0f2f6;padding:10px 5px;'>
        <marquee scrollamount='5' behavior='scroll' direction='left'>
            {0}
        </marquee>
    </div>
""".format(header_marquee), unsafe_allow_html=True)

# Sidebar - Top Movers
with st.sidebar:
    st.header("📊 Top Movers")

    def get_top_movers():
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        try:
            gainer_url = "https://www.nseindia.com/api/live-analysis-variations?index=gainers"
            loser_url = "https://www.nseindia.com/api/live-analysis-variations?index=losers"
            session = requests.Session()
            session.headers.update(headers)
            gainer_data = session.get(gainer_url).json()["data"]
            loser_data = session.get(loser_url).json()["data"]

            top_gainers = pd.DataFrame(gainer_data)[['symbol', 'ltp', 'netPrice']].head(5)
            top_losers = pd.DataFrame(loser_data)[['symbol', 'ltp', 'netPrice']].head(5)

            return top_gainers, top_losers
        except Exception as e:
            return None, None

    gainers, losers = get_top_movers()

    if gainers is not None:
        st.subheader("🔼 Top Gainers")
        for _, row in gainers.iterrows():
            st.markdown(f"**{row['symbol']}** - ₹{row['ltp']} ({row['netPrice']}%)")

        st.subheader("🔽 Top Losers")
        for _, row in losers.iterrows():
            st.markdown(f"**{row['symbol']}** - ₹{row['ltp']} ({row['netPrice']}%)")
    else:
        st.warning("Could not load top movers. Try again later.")

# Title
st.title("📈 Live Stock Analysis Dashboard")

# Load Nifty 500 list
url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
nifty_df = pd.read_csv(url)
nifty_df["Symbol_NS"] = nifty_df["Symbol"] + ".NS"

# Company dropdown
selected_company = st.selectbox("Select a Company", nifty_df["Company Name"].tolist())
selected_symbol = nifty_df[nifty_df["Company Name"] == selected_company]["Symbol_NS"].values[0]

# Fetch data
data = yf.download(selected_symbol, period="1d", interval="5m")

if data.empty or "Close" not in data.columns:
    st.error("❌ Live data not available at the moment. Please try again later or during market hours.")
else:
    # Convert index to IST timezone (Asia/Kolkata) if not already tz-aware
    if data.index.tz is None:
        data.index = data.index.tz_localize('UTC').tz_convert('Asia/Kolkata')
    else:
        data.index = data.index.tz_convert('Asia/Kolkata')

    data['Time'] = data.index.strftime('%H:%M:%S')

    # EMA Calculation
    data['EMA_9'] = data['Close'].ewm(span=9, adjust=False).mean()
    data['EMA_15'] = data['Close'].ewm(span=15, adjust=False).mean()
    data['Signal'] = 0
    data.loc[data['EMA_9'] > data['EMA_15'], 'Signal'] = 1
    data.loc[data['EMA_9'] < data['EMA_15'], 'Signal'] = -1
    data['Crossover'] = data['Signal'].diff()

    # Show live price with timestamp
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
    bullish = data[data['Crossover'] == 2]
    bearish = data[data['Crossover'] == -2]

    ax.scatter(bullish.index, bullish['Close'], marker='^', color='green', s=100, label='Bullish Crossover')
    ax.scatter(bearish.index, bearish['Close'], marker='v', color='red', s=100, label='Bearish Crossover')

    # X-axis formatting to show only time in IST
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
