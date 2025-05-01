# app.py

import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import time
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

st.set_page_config(layout="wide")
st.title("📊 Reliance Stock: EMA Crossover + ML Signal")

# --- Step 1: Fetch Data with Retry & Cache ---
@st.cache_data(ttl=900)  # cache for 15 minutes
def fetch_data(ticker):
    while True:
        try:
            data = yf.download(ticker, period='30d', interval='15m', auto_adjust=True)
            if data.empty:
                raise Exception("Empty DataFrame")
            return data
        except Exception as e:
            st.warning(f"Retrying in 10s due to: {e}")
            time.sleep(10)

ticker = 'RELIANCE.NS'
data = fetch_data(ticker)

# --- Step 2: EMA Calculation ---
data['EMA9'] = data['Close'].ewm(span=9, adjust=False).mean()
data['EMA15'] = data['Close'].ewm(span=15, adjust=False).mean()

# --- Step 3: Generate Signals ---
data['Signal'] = 0
data.loc[data['EMA9'] > data['EMA15'], 'Signal'] = 1
data['Position'] = data['Signal'].diff()

# --- Step 4: ML Features ---
data['Return'] = data['Close'].pct_change()
data['EMA_diff'] = data['EMA9'] - data['EMA15']
data.dropna(inplace=True)

X = data[['EMA_diff', 'Return']]
y = data['Signal']

if len(X) < 10:
    st.error("❌ Not enough data. Try using a longer period or lower frequency.")
    st.stop()

# --- Step 5: Train Model ---
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
model = RandomForestClassifier()
model.fit(X_train, y_train)
pred = model.predict(X_test)
acc = round(accuracy_score(y_test, pred), 4)

st.success(f"✅ Model Accuracy: {acc}")

# --- Step 6: Predict Latest Signal ---
latest = X.iloc[[-1]]
prediction = model.predict(latest)[0]
if prediction == 1:
    st.markdown("### 📈 **Bullish Signal (Buy)**")
else:
    st.markdown("### 📉 **Bearish Signal (Sell)**")

# --- Step 7: Plot Chart ---
fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(data['Close'], label='Close Price', color='blue', alpha=0.6)
ax.plot(data['EMA9'], label='EMA 9', color='green')
ax.plot(data['EMA15'], label='EMA 15', color='red')

# Crossover markers
ax.scatter(data.index[data['Position'] == 1], data['Close'][data['Position'] == 1], marker='^', color='green', label='Bullish Crossover', s=100)
ax.scatter(data.index[data['Position'] == -1], data['Close'][data['Position'] == -1], marker='v', color='red', label='Bearish Crossover', s=100)

ax.set_title(f'{ticker} EMA Crossover + ML Signal')
ax.set_xlabel('Time')
ax.set_ylabel('Price')
ax.legend()
ax.grid(True)
st.pyplot(fig)
