import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Define stock pairs (AMD & NVDA)
stocks = ["AMD", "NVDA"]

# Define date range
end_date = pd.to_datetime("03/15/2024")
start_date = end_date - pd.DateOffset(months=15)

# Download stock data
data = yf.download(stocks, start=start_date, end=end_date)["Close"]

# Compute the price spread (ratio method)
spread = data["AMD"] / data["NVDA"]

# Compute moving average & standard deviation of spread
spread_mean = spread.rolling(window=50).mean()
spread_std = spread.rolling(window=50).std()

# Compute Z-score (standardized spread)
spread_zscore = (spread - spread_mean) / spread_std

# Define trading signals
long_signal = spread_zscore <= -1.3  # Buy NVDA, Short AMD
short_signal = spread_zscore >= 1.3   # Buy AMD, Short NVDA
exit_signal = abs(spread_zscore) < 0.5  # Close positions

# Initialize tracking variables
capital = 5000  # Initial capital
current_capital = capital
amd_positions = []
nvda_positions = []
amd_short_positions = []
nvda_short_positions = []
trade_details = []  # To store trade details
cumulative_returns = []

# Function to calculate trade profit
def trade_profit(entry_price, exit_price, short=False):
    if short:
        return 1 + ((entry_price - exit_price) / entry_price)
    else:
        return 1 + ((exit_price - entry_price) / entry_price)

# Track portfolio value
portfolio_value = 0

# To track the buy, short, and exit events for graph markers
buy_signals = []
short_signals = []
exit_signals = []

for i in range(len(data)):
    # Long NVDA, Short AMD
    if long_signal.iloc[i] and current_capital >= 1000:
        nvda_positions.append((data.iloc[i]["NVDA"], (current_capital/2) / data.iloc[i]["NVDA"]))  # Buy NVDA
        amd_short_positions.append((data.iloc[i]["AMD"], (current_capital/2) / data.iloc[i]["AMD"]))  # Short AMD
        current_capital = 0
        trade_details.append({'Date': data.index[i], 'Stock': 'NVDA', 'Action': 'Buy', 'Entry Price': data.iloc[i]["NVDA"], 'Position': (current_capital/2) / data.iloc[i]["NVDA"], 'Profit': None, 'Exit Price': None})
        trade_details.append({'Date': data.index[i], 'Stock': 'AMD', 'Action': 'Short', 'Entry Price': data.iloc[i]["AMD"], 'Position': (current_capital/2) / data.iloc[i]["AMD"], 'Profit': None, 'Exit Price': None})
        buy_signals.append(data.index[i])  # Record buy signal for NVDA
    
    # Long AMD, Short NVDA
    elif short_signal.iloc[i] and current_capital >= 1000:
        amd_positions.append((data.iloc[i]["AMD"], (current_capital/2) / data.iloc[i]["AMD"]))  # Buy AMD
        nvda_short_positions.append((data.iloc[i]["NVDA"], (current_capital/2) / data.iloc[i]["NVDA"]))  # Short NVDA
        current_capital = 0
        trade_details.append({'Date': data.index[i], 'Stock': 'AMD', 'Action': 'Buy', 'Entry Price': data.iloc[i]["AMD"], 'Position': (current_capital/2) / data.iloc[i]["AMD"], 'Profit': None, 'Exit Price': None})
        trade_details.append({'Date': data.index[i], 'Stock': 'NVDA', 'Action': 'Short', 'Entry Price': data.iloc[i]["NVDA"], 'Position': (current_capital/2) / data.iloc[i]["NVDA"], 'Profit': None, 'Exit Price': None})
        short_signals.append(data.index[i])  # Record short signal for NVDA
    
    # Close positions when exit signal triggers
    if exit_signal.iloc[i]:
        # For long positions (AMD and NVDA)
        for entry_price, position in amd_positions:
            profit = trade_profit(entry_price, data.iloc[i]["AMD"])
            trade_details.append({'Date': data.index[i], 'Stock': 'AMD', 'Action': 'Sell', 'Entry Price': entry_price, 'Position': position, 'Profit': profit, 'Exit Price': data.iloc[i]["AMD"]})
            current_capital += position * entry_price * profit  # Add the profit from closing this position

        for entry_price, position in nvda_positions:
            profit = trade_profit(entry_price, data.iloc[i]["NVDA"])
            trade_details.append({'Date': data.index[i], 'Stock': 'NVDA', 'Action': 'Sell', 'Entry Price': entry_price, 'Position': position, 'Profit': profit, 'Exit Price': data.iloc[i]["NVDA"]})
            current_capital += position * entry_price * profit  # Add the profit from closing this position

        # For short positions (AMD and NVDA)
        for entry_price, position in amd_short_positions:
            profit = trade_profit(entry_price, data.iloc[i]["AMD"], short=True)
            trade_details.append({'Date': data.index[i], 'Stock': 'AMD', 'Action': 'Cover Short', 'Entry Price': entry_price, 'Position': position, 'Profit': profit, 'Exit Price': data.iloc[i]["AMD"]})
            current_capital +=  position * entry_price * profit  # Add the profit from closing the short position

        for entry_price, position in nvda_short_positions:
            profit = trade_profit(entry_price, data.iloc[i]["NVDA"], short=True)
            trade_details.append({'Date': data.index[i], 'Stock': 'NVDA', 'Action': 'Cover Short', 'Entry Price': entry_price, 'Position': position, 'Profit': profit, 'Exit Price': data.iloc[i]["NVDA"]})
            current_capital += position * entry_price * profit  # Add the profit from closing the short position

        # Clear positions after exit
        amd_positions.clear()
        nvda_positions.clear()
        amd_short_positions.clear()
        nvda_short_positions.clear()

        exit_signals.append(data.index[i])  # Record exit signal

    # Track portfolio value (open positions)
    portfolio_value = sum([pos[1] * data.iloc[i]["AMD"] for pos in amd_positions]) + \
                      sum([pos[1] * data.iloc[i]["NVDA"] for pos in nvda_positions])
    cumulative_returns.append(sum([trade['Profit'] for trade in trade_details if trade['Profit'] is not None]) + portfolio_value + current_capital)

# Create DataFrame for trade details
trades_df = pd.DataFrame(trade_details)

# Export trade details to Excel
trades_df.to_excel("pairs_trading_trades_with_exit_prices.xlsx", index=False)

# Compute final returns
strategy_returns = sum([trade['Profit'] for trade in trade_details if trade['Profit'] is not None]) + portfolio_value + current_capital
print("Total Strategy Returns: $", round(strategy_returns, 2))

# Plot results
plt.figure(figsize=(12, 8))

# Spread Z-Score with signals
plt.subplot(3, 1, 1)
plt.plot(data.index, spread_zscore, label='Spread Z-Score', color='blue')
plt.axhline(1.3, color='red', linestyle='--', label='Short Signal')
plt.axhline(-1.3, color='green', linestyle='--', label='Long Signal')
plt.axhline(0.5, color='black', linestyle='dotted', label='Exit Signal')
plt.axhline(-0.5, color='black', linestyle='dotted')
plt.scatter(buy_signals, spread_zscore.loc[buy_signals], marker='^', color='green', label='Buy NVDA')
plt.scatter(short_signals, spread_zscore.loc[short_signals], marker='v', color='red', label='Short NVDA')
plt.scatter(exit_signals, spread_zscore.loc[exit_signals], marker='x', color='black', label='Exit')
plt.legend()
plt.title('Spread Z-Score & Trading Signals')

# Stock Prices
plt.subplot(3, 1, 2)
plt.plot(data.index, data['AMD'], label='AMD Price', color='purple')
plt.plot(data.index, data['NVDA'], label='NVDA Price', color='orange')
plt.legend()
plt.title('Stock Prices')

# Cumulative Returns
plt.subplot(3, 1, 3)
plt.plot(data.index, cumulative_returns, label='Cumulative Returns', color='black')
plt.legend()
plt.title('Cumulative Returns')

plt.tight_layout()
plt.show()
