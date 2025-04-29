import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import pytz
import time

# Set wide layout
st.set_page_config(layout="wide")
st.title("📈 Advanced Stock Analysis Dashboard")

# === Sidebar Options ===
with st.sidebar:
    st.header("⚙️ Settings")

    refresh = st.checkbox("Auto Refresh Every 60s", value=True)
    period = st.selectbox("Select Time Period", ["1d", "5d", "1mo", "3mo", "6mo", "1y"], index=0)
    interval = st.selectbox("Select Interval", ["1m", "5m", "15m", "1h", "1d"], index=1)
    chart_type = st.radio("Chart Type", ["Line", "Candlestick"], index=0)
    show_rsi = st.checkbox("Show RSI Indicator", value=True)

    # Auto-refresh logic
    rerun_interval = 60
    if refresh:
        if "rerun_time" not in st.session_state:
            st.session_state.rerun_time = time.time()
        if time.time() - st.session_state.rerun_time > rerun_interval:
            st.session_state.rerun_time = time.time()
            st.experimental_rerun()

# === Load Nifty 500 Data ===
url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
nifty_df = pd.read_csv(url)
nifty_df["Symbol_NS"] = nifty_df["Symbol"] + ".NS"

# === Company Selector ===
selected_company = st.selectbox("Select a Company", nifty_df["Company Name"].tolist())
selected_symbol = nifty_df[nifty_df["Company Name"] == selected_company]["Symbol_NS"].values[0]

# === Fetch Data ===
data = yf.download(selected_symbol, period=period, interval=interval)

if data.empty or "Close" not in data.columns:
    st.error("❌ Data not available. Try different time or during market hours.")
else:
    # === Convert to IST ===
    data.index = data.index.tz_localize('UTC').tz_convert('Asia/Kolkata')
    data['Time'] = data.index.strftime('%H:%M:%S')

    # === EMA Calculation ===
    data['EMA_9'] = data['Close'].ewm(span=9, adjust=False).mean()
    data['EMA_15'] = data['Close'].ewm(span=15, adjust=False).mean()
    data['Signal'] = 0
    data.loc[data['EMA_9'] > data['EMA_15'], 'Signal'] = 1
    data.loc[data['EMA_9'] < data['EMA_15'], 'Signal'] = -1
    data['Crossover'] = data['Signal'].diff()

    # === RSI Calculation ===
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    data['RSI'] = 100 - (100 / (1 + rs))

    # === Live Price Display ===
    latest_price = float(data['Close'].iloc[-1])
    prev_price = float(data['Close'].iloc[-2])
    delta_price = latest_price - prev_price
    latest_time = data.index[-1].strftime('%H:%M:%S')

    st.metric(label="Current Price", value=f"₹ {latest_price:.2f}", delta=f"{delta_price:.2f} (as of {latest_time})")

    # === Chart Display ===
    st.subheader(f"{selected_symbol} – {chart_type} Chart with EMA")

    if chart_type == "Line":
        st.line_chart(data[['Close', 'EMA_9', 'EMA_15']])
    else:
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name='Candlestick'
        ))
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA_9'], mode='lines', name='EMA 9', line=dict(color='green')))
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA_15'], mode='lines', name='EMA 15', line=dict(color='red')))
        fig.update_layout(xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

    # === RSI Chart ===
    if show_rsi:
        st.subheader("📉 RSI (Relative Strength Index)")
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=data.index, y=data['RSI'], line=dict(color='orange'), name="RSI"))
        fig_rsi.update_layout(
            yaxis=dict(range=[0, 100]),
            shapes=[
                dict(type='line', x0=data.index[0], x1=data.index[-1], y0=70, y1=70, line=dict(dash='dash', color='red')),
                dict(type='line', x0=data.index[0], x1=data.index[-1], y0=30, y1=30, line=dict(dash='dash', color='green'))
            ]
        )
        st.plotly_chart(fig_rsi, use_container_width=True)

    # === Signal Alert ===
    st.subheader("📢 Signal Alert")
    last_signal = data['Crossover'].iloc[-1]
    if last_signal == 2:
        st.success("✅ Bullish Crossover (Buy Signal)")
    elif last_signal == -2:
        st.error("⚠️ Bearish Crossover (Sell Signal)")
    else:
        st.info("No crossover signal currently")

    # === Data Table and Download ===
    st.subheader("📋 Latest Data Snapshot")
    st.dataframe(data[['Close', 'EMA_9', 'EMA_15', 'RSI']].tail(10))

    csv = data.to_csv().encode('utf-8')
    st.download_button("⬇️ Download Data", csv, file_name=f'{selected_symbol}_data.csv', mime='text/csv')
