# app.py

import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

st.title("📊 Reliance Live EMA Crossover & ML Trend Predictor")

# Load data
ticker = yf.Ticker("RELIANCE.NS")
data = ticker.history(period="1d", interval="5m")

# Feature engineering
data['Price_Change'] = data['Close'].diff()
data['Target'] = (data['Price_Change'] > 0).astype(int)
data['EMA_9'] = data['Close'].ewm(span=9, adjust=False).mean()
data['EMA_15'] = data['Close'].ewm(span=15, adjust=False).mean()
data.dropna(inplace=True)

# ML Model
X = data[['Open', 'High', 'Low', 'Close', 'Volume']]
y = data['Target']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

model = RandomForestClassifier()
model.fit(X_train, y_train)
predictions = model.predict(X_test)
acc = accuracy_score(y_test, predictions)

st.subheader(f"📈 ML Model Accuracy: {acc:.2f}")

# EMA crossover detection
data['Signal'] = 0
data.loc[data['EMA_9'] > data['EMA_15'], 'Signal'] = 1
data.loc[data['EMA_9'] < data['EMA_15'], 'Signal'] = -1
data['Crossover'] = data['Signal'].diff()

# Plotting
fig, ax = plt.subplots(figsize=(14, 8))
ax.plot(data.index, data['Close'], label='Close Price', color='blue', alpha=0.5)
ax.plot(data.index, data['EMA_9'], label='EMA 9', color='green')
ax.plot(data.index, data['EMA_15'], label='EMA 15', color='red')

# Mark crossovers
bullish = data[data['Crossover'] == 2]
bearish = data[data['Crossover'] == -2]

ax.scatter(bullish.index, bullish['Close'], marker='^', color='green', label='Bullish Crossover', s=100)
ax.scatter(bearish.index, bearish['Close'], marker='v', color='red', label='Bearish Crossover', s=100)

# Draw lines
for idx in bullish.index:
    ax.plot([idx, idx], [bullish.loc[idx, 'EMA_9'], bullish.loc[idx, 'EMA_15']], 'g--')

for idx in bearish.index:
    ax.plot([idx, idx], [bearish.loc[idx, 'EMA_9'], bearish.loc[idx, 'EMA_15']], 'r--')

ax.set_title('Reliance Stock with EMA Crossovers')
ax.set_xlabel('Time')
ax.set_ylabel('Price')
ax.legend()
ax.grid(True)
st.pyplot(fig)
