import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
import time
from plotly.subplots import make_subplots
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="📈 Live Stock Analysis Dashboard", page_icon="📈")

# Auto-refresh every 60 seconds
rerun_interval = 60
if "rerun_time" not in st.session_state:
    st.session_state.rerun_time = time.time()

if time.time() - st.session_state.rerun_time > rerun_interval:
    st.session_state.rerun_time = time.time()
    st.experimental_rerun()

# Title
st.markdown("<h1 style='text-align: center; color: #2c3e50;'>📈 Live Stock Analysis Dashboard</h1>", unsafe_allow_html=True)
st.markdown("---")

# Live indices: NIFTY 50 & BANK NIFTY
index_symbols = {
    "NIFTY 50": "^NSEI",
    "BANK NIFTY": "^NSEBANK"
}
index_data = {}
for name, symbol in index_symbols.items():
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="1d", interval="5m")
    if not hist.empty:
        index_data[name] = hist['Close'].iloc[-1]
    else:
        index_data[name] = None

col1, col2 = st.columns(2)
with col1:
    st.metric(label="🌟 NIFTY 50", value=f"{index_data['NIFTY 50']:.2f}" if index_data["NIFTY 50"] else "N/A")
with col2:
    st.metric(label="🏦 BANK NIFTY", value=f"{index_data['BANK NIFTY']:.2f}" if index_data["BANK NIFTY"] else "N/A")

st.markdown("---")

# Load Nifty 500 list
@st.cache_data
def load_nifty_500():
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    df = pd.read_csv(url)
    df["Symbol_NS"] = df["Symbol"] + ".NS"
    return df

nifty_df = load_nifty_500()

# Company selection
selected_company = st.selectbox(
    "🔎 Search and Select a Company",
    nifty_df["Company Name"].tolist(),
    index=None,
    placeholder="Type to search..."
)

if selected_company:
    selected_symbol = nifty_df[nifty_df["Company Name"] == selected_company]["Symbol_NS"].values[0]

    # Fetch data
    data = yf.download(selected_symbol, period="1d", interval="5m")

    if data.empty or "Close" not in data.columns:
        st.error("❌ Live data not available at the moment. Please try again later or during market hours.")
    else:
        # Convert index to IST
        data.index = data.index.tz_convert('Asia/Kolkata')

        # EMA calculation
        data['EMA_9'] = data['Close'].ewm(span=9, adjust=False).mean()
        data['EMA_15'] = data['Close'].ewm(span=15, adjust=False).mean()
        data['Signal'] = 0
        data.loc[data['EMA_9'] > data['EMA_15'], 'Signal'] = 1
        data.loc[data['EMA_9'] < data['EMA_15'], 'Signal'] = -1
        data['Crossover'] = data['Signal'].diff()

        # Current price
        try:
            latest_price = float(data['Close'].iloc[-1])
            latest_time = data.index[-1].strftime('%H:%M:%S')
            st.metric(label=f"📊 {selected_company} Current Price", value=f"₹ {latest_price:.2f}", delta=f"As of {latest_time} IST")
        except:
            st.metric(label="📊 Current Price", value="N/A", delta="Unavailable")

        # --- Plotly Candlestick Chart with EMA & Volume ---
        st.subheader(f"{selected_symbol} - Candlestick Chart with EMA + Volume")

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                            vertical_spacing=0.02, row_heights=[0.7, 0.3],
                            specs=[[{"type": "candlestick"}],
                                   [{"type": "bar"}]])

        # Candlestick
        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name="Price",
            increasing_line_color='green',
            decreasing_line_color='red'
        ), row=1, col=1)

        # EMA lines
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['EMA_9'],
            line=dict(color='blue', width=1),
            name='EMA 9'
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['EMA_15'],
            line=dict(color='orange', width=1),
            name='EMA 15'
        ), row=1, col=1)

        # Volume bars
        colors = ['green' if c >= o else 'red' for c, o in zip(data['Close'], data['Open'])]
        fig.add_trace(go.Bar(
            x=data.index,
            y=data['Volume'],
            marker_color=colors,
            name='Volume'
        ), row=2, col=1)

        fig.update_layout(
            height=700,
            xaxis_rangeslider_visible=False,
            showlegend=True,
            plot_bgcolor='white',
            margin=dict(t=40, b=40),
            xaxis=dict(type="category")
        )

        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("🔔 Please search and select a company to view its live analysis.")
