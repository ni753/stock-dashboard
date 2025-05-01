import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import time

# --- Step 1: Safe Download (handle rate limit) ---
def fetch_data(ticker):
    while True:
        try:
            data = yf.download(ticker, period='30d', interval='15m', auto_adjust=True)
            if data.empty:
                raise Exception("Empty DataFrame")
            return data
        except Exception as e:
            print(f"Retrying due to error: {e}")
            time.sleep(10)

ticker = 'RELIANCE.NS'
data = fetch_data(ticker)

# --- Step 2: EMA Calculation ---
data['EMA9'] = data['Close'].ewm(span=9, adjust=False).mean()
data['EMA15'] = data['Close'].ewm(span=15, adjust=False).mean()

# --- Step 3: Signal Generation (fixed warning with .loc) ---
data['Signal'] = 0
data.loc[data['EMA9'] > data['EMA15'], 'Signal'] = 1
data['Position'] = data['Signal'].diff()

# --- Step 4: Features for ML ---
data['Return'] = data['Close'].pct_change()
data['EMA_diff'] = data['EMA9'] - data['EMA15']
data.dropna(inplace=True)

X = data[['EMA_diff', 'Return']]
y = data['Signal']

if len(X) < 10:
    raise ValueError("Not enough data after feature engineering. Try longer period or lower interval.")

# --- Step 5: Train ML Model ---
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

model = RandomForestClassifier()
model.fit(X_train, y_train)
pred = model.predict(X_test)

print("✅ Accuracy:", round(accuracy_score(y_test, pred), 4))

# --- Step 6: Prediction for Latest ---
latest = X.iloc[[-1]]
prediction = model.predict(latest)[0]

if prediction == 1:
    print("📈 Signal: Bullish crossover likely (Buy)")
else:
    print("📉 Signal: Bearish crossover likely (Sell)")

# --- Optional: Plotting ---
plt.figure(figsize=(14, 6))
plt.plot(data['Close'], label='Close Price', color='blue', alpha=0.6)
plt.plot(data['EMA9'], label='EMA 9', color='green')
plt.plot(data['EMA15'], label='EMA 15', color='red')
plt.scatter(data.index[data['Position'] == 1], data['Close'][data['Position'] == 1], marker='^', color='green', label='Bullish Crossover', s=100)
plt.scatter(data.index[data['Position'] == -1], data['Close'][data['Position'] == -1], marker='v', color='red', label='Bearish Crossover', s=100)
plt.title(f'{ticker} EMA Crossover + ML Prediction')
plt.xlabel('Time')
plt.ylabel('Price')
plt.legend()
plt.grid()
plt.tight_layout()
plt.show()
