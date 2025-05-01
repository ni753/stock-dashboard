import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pytz

st.set_page_config(layout="wide")
st.title("📈 Live Buy/Sell Signal Generator Using EMA Crossover")

# Load Nifty 500 list
@st.cache_data
def load_nifty_500():
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    df = pd.read_csv(url)
    df["Symbol_NS"] = df["Symbol"] + ".NS"
    return df

nifty_df = load_nifty_500()
selected_company = st.selectbox("Select a Company", nifty_df["Company Name"].tolist())
selected_symbol = nifty_df[nifty_df["Company Name"] == selected_company]["Symbol_NS"].values[0]

# Fetch Data
data = yf.download(selected_symbol, period="5d", interval="15m")

if data.empty or "Close" not in data.columns:
    st.warning("⚠️ Data unavailable. Try during market hours.")
    st.stop()

# Convert time to IST
data.index = data.index.tz_convert('Asia/Kolkata')
data['Time'] = data.index.strftime('%Y-%m-%d %H:%M')

# EMA Calculation
data['EMA_9'] = data['Close'].ewm(span=9, adjust=False).mean()
data['EMA_15'] = data['Close'].ewm(span=15, adjust=False).mean()
data['Signal'] = 0
data.loc[data['EMA_9'] > data['EMA_15'], 'Signal'] = 1
data.loc[data['EMA_9'] < data['EMA_15'], 'Signal'] = -1
data['Crossover'] = data['Signal'].diff()

# Buy/Sell Points
buy_signals = data[data['Crossover'] == 2]
sell_signals = data[data['Crossover'] == -2]

# Plot
st.subheader("📊 EMA Crossover Chart with Buy/Sell Signals")

fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(data.index, data['Close'], label='Close Price', color='blue', alpha=0.6)
ax.plot(data.index, data['EMA_9'], label='EMA 9', color='green')
ax.plot(data.index, data['EMA_15'], label='EMA 15', color='red')

ax.scatter(buy_signals.index, buy_signals['Close'], marker='^', color='green', s=120, label='Buy Signal')
ax.scatter(sell_signals.index, sell_signals['Close'], marker='v', color='red', s=120, label='Sell Signal')

ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M', tz=pytz.timezone("Asia/Kolkata")))
fig.autofmt_xdate()

ax.set_xlabel("Time (IST)")
ax.set_ylabel("Price")
ax.legend()
st.pyplot(fig)
