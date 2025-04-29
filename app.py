import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import pytz
import time

st.set_page_config(page_title="📈 Live Stock Dashboard", layout="wide")

# Auto-refresh every 60 seconds
rerun_interval = 60
if "rerun_time" not in st.session_state:
    st.session_state.rerun_time = time.time()

if time.time() - st.session_state.rerun_time > rerun_interval:
    st.session_state.rerun_time = time.time()
    st.experimental_rerun()

# Load Nifty 500 list
@st.cache_data(ttl=3600)
def load_nifty500():
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    df = pd.read_csv(url)
    df["Symbol_NS"] = df["Symbol"] + ".NS"
    return df

nifty_df = load_nifty500()

# Sidebar
st.sidebar.header("⚙️ Controls")
selected_company = st.sidebar.selectbox("Select a Company", nifty_df["Company Name"].tolist())
selected_symbol = nifty_df[nifty_df["Company Name"] == selected_company]["Symbol_NS"].values[0]

# Main title
st.title("📈 Live Stock Analysis Dashboard")
st.markdown("Get real-time price, EMA crossover signals, and candlestick chart.")

# Fetch stock data
data = yf.download(selected_symbol, period="1d", interval="5m")

if data.empty or "Close" not in data.columns:
    st.error("❌ Live data not available at the moment. Please try again later or during market hours.")
else:
    # Convert index to IST timezone
    data.index = data.index.tz_convert('Asia/Kolkata')
    data['Time'] = data.index.strftime('%H:%M:%S')

    # EMA calculation
    data['EMA_9'] = data['Close'].ewm(span=9, adjust=False).mean()
    data['EMA_15'] = data['Close'].ewm(span=15, adjust=False).mean()
    data['Signal'] = 0
    data.loc[data['EMA_9'] > data['EMA_15'], 'Signal'] = 1
    data.loc[data['EMA_9'] < data['EMA_15'], 'Signal'] = -1
    data['Crossover'] = data['Signal'].diff()

    # Live price
    latest_price = float(data['Close'].iloc[-1])
    latest_time = data.index[-1].strftime('%H:%M:%S')

    st.metric(label=f"💰 Current Price of {selected_symbol}", value=f"₹ {latest_price:.2f}", delta=f"As of {latest_time} IST")

    # Candlestick chart with EMA overlays and crossover points
    st.subheader("🕯️ Candlestick Chart with EMA Crossovers")

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='Candles'
    ))

    fig.add_trace(go.Scatter(
        x=data.index, y=data['EMA_9'],
        line=dict(color='green', width=1.5), name='EMA 9'
    ))

    fig.add_trace(go.Scatter(
        x=data.index, y=data['EMA_15'],
        line=dict(color='red', width=1.5), name='EMA 15'
    ))

    # Crossover points
    bullish = data[data['Crossover'] == 2]
    bearish = data[data['Crossover'] == -2]

    fig.add_trace(go.Scatter(
        x=bullish.index, y=bullish['Close'],
        mode='markers',
        marker=dict(color='lime', size=10, symbol='triangle-up'),
        name='Bullish Crossover'
    ))

    fig.add_trace(go.Scatter(
        x=bearish.index, y=bearish['Close'],
        mode='markers',
        marker=dict(color='red', size=10, symbol='triangle-down'),
        name='Bearish Crossover'
    ))

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        plot_bgcolor='white',
        hovermode='x unified',
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    fig.update_xaxes(title_text="Time (IST)")
    fig.update_yaxes(title_text="Price", showgrid=True, gridcolor='lightgray')

    st.plotly_chart(fig, use_container_width=True)
