import yfinance as yf
import pandas as pd
import datetime

# Define the tickers
tickers = [
"UBER", "UNH",  "JD",   "AVGO", "TRGP", "OKE",  "ARRY", "COST", "PGR",
"CHRD", "NE",   "GPOR", "SABR", "PSX",  "TAL",  "ISRG", "DINO", "LNG",  "PAGP",
"PR",   "ANET", "FANG", "FSLR", "CVNA", "PG",   "LUV",  "SBUX", "NFLX", "LLY",
"VRTX", "HUM",  "TSEM", "OVV",  "PPL",  "CVX",  "MELI", "VLO",  "SMCI", "CRM",
"MKL",  "DIS",  "HAL",  "BKNG", "NOW",  "PYPL", "SPOT", "VTI",  
"SRLN", "GWRE", "ALV",  "HAS",  "ADNT", "LBTYA",        "CSTM", "EQT",  "EPD",  "ASO",
"BAC",  "JOE",  "NPWR", "TDG",  "ADBE", "JPM",  "ELV",  "TECK", "SHEL", "CSCO",
"KMI",  "MCO",  "TSM",  "BNTX", "AMD",  "PDD",  "ORCL", "EDU",  "CACC",
"SNX",  "INTC", "KLAC", "NVDA", "BRK-B",        "AMAT", "WFC",  "MRNA", "IBKR", "AAPL",
"TSLA", "SPGI", "V",    "BABA", "MA",   "AMZN", "GOOG", "META", "GOOGL",        "MSFT",
]

tickers = [
"AR", "AVGO", "CVE", "CRH", "ELV", "XOM", "VRT", "V",
]

# Custom initial weights (example)
custom_weights = {
"INTC":0.50,    "MATV":0.38,    "NIO":0.41,     "CHTR":1.39,    "CRL":0.32,     "GPN":1.59,     "PYPL":0.64,    "TXN":0.93,     "GOOG":3.85,    "AMD":0.53,
"V":2.03,       "MA":1.92,      "ARKK":0.67,    "PATH":0.28,    "PDD":0.87,     "MRAAY":0.47,   "TLT":11.54,    "RYAAY":1.90,   "ROKU":0.68,    "LYFT":1.34,
"AMZN":4.64,    "PFO":1.12,     "WMMVY":1.45,   "ENB":1.85,     "KCKSF":0.44,   "DT":1.15,      "CAH":3.68,     "KWEB":0.78,    "OKTA":0.64,    "JD":1.55,
"FVRR":0.25,    "UBER":1.84,    "MO":1.10,      "AI":1.09,      "AL":1.98,      "KOF":2.10,     "ATHM":1.27,    "BIDU":0.93,    "CRM":1.15,     "MRNA":0.06,
"XYZ":0.55,     "HII":1.55,     "MELI":5.11,    "FSLY":0.52,
}

# Use only tickers from custom weights
tickers = list(custom_weights.keys())

# Set the backtest period (1 year)
end_date = datetime.datetime.today()
start_date = end_date - datetime.timedelta(days=365)

# Download daily adjusted close prices
data = yf.download(tickers, start=start_date, end=end_date,  interval="1mo")["Close"]

# Drop rows with missing values across all tickers
data = data.dropna()

# Resample to get last trading day of each month
monthly_data = data.resample('M').last()

# Normalize prices (start at 1)
normalized_data = monthly_data / monthly_data.iloc[0]

# Sort columns of normalized_data by yearly performance
final_prices = monthly_data.iloc[-1]
initial_prices = monthly_data.iloc[0]
returns = (final_prices - initial_prices) / initial_prices * 100
sorted_columns = returns.sort_values(ascending=False).index
normalized_data = normalized_data[sorted_columns]

# Apply custom weights
weights = pd.Series(0, index=normalized_data.columns)
for symbol, weight in custom_weights.items():
    if symbol in weights.index:
        weights[symbol] = weight / 100

# Calculate cash allocation if total weight < 100%
total_weight = weights.sum()
cash_weight = 1.0 - total_weight if total_weight < 1.0 else 0.0

# Normalize weights if total is > 0
if total_weight > 0:
    weights = weights / (weights.sum() + cash_weight)

if cash_weight > 0:
    weights["FDRXX"] = cash_weight
print("\nInitial Weights:")
print(weights.sort_values(ascending=False).to_string())

# Calculate weighted portfolio value
portfolio_value = (normalized_data * weights).sum(axis=1)

# Add cash yield over time if applicable
if cash_weight > 0:
    monthly_yield = (1 + 0.05) ** (1/12) - 1  # approximate monthly compounding
    months = len(portfolio_value)
    cash_growth = [(1 + monthly_yield) ** i for i in range(months)]
    cash_series = pd.Series(cash_growth, index=portfolio_value.index)
    portfolio_value += cash_weight * cash_series

    # Add cash to normalized data and weights under ticker FDRXX
    normalized_data["FDRXX"] = cash_series / cash_series.iloc[0]
    weights["FDRXX"] = cash_weight

# Calculate monthly returns
monthly_returns = portfolio_value.pct_change() * 100  # in percent

# Combine into a single DataFrame
summary = pd.DataFrame({
    "Portfolio Value": portfolio_value,
    "Monthly Return (%)": monthly_returns
})

# Print normalized prices (optional)
print("\nNormalized Prices (Sorted by Yearly Performance):\n", normalized_data)

# Print monthly retrospective
print("\nMonthly Retrospective:\n", summary)


# Calculate and print top 10 performing stocks
final_prices = normalized_data.iloc[-1]
initial_prices = normalized_data.iloc[0]
total_returns = (final_prices - initial_prices) / initial_prices * 100
top_10 = total_returns.sort_values(ascending=False).head(10)
print("\nTop 10 Best-Performing Stocks over 1 Year:")
print(top_10.to_string())

# Calculate and print total return
initial_value = portfolio_value.iloc[0]
final_value = portfolio_value.iloc[-1]
total_return = (final_value - initial_value) / initial_value * 100
print(f"\nTotal Portfolio Return over 1 Year: {total_return:.2f}%")
