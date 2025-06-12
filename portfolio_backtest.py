import yfinance as yf
import pandas as pd
import datetime
import argparse
import sys

# Define default custom portfolio weights as a percentage of total capital
custom_weights = {
    "FTEC": 20, "IYW": 20, "IGM": 20, "IGV": 20, "VGT": 20, "QQQ": 20
}

def main():
    global cmd_args

    # Determine tickers and weights based on user input
    if cmd_args.equalweight:
        tickers = cmd_args.equalweight
        weights = pd.Series(1 / len(tickers), index=tickers)
    elif cmd_args.weighted:
        custom_input = dict(item.split(':') for item in cmd_args.weighted)
        tickers = list(custom_input.keys())
        weights = pd.Series({k: float(v)/100 for k, v in custom_input.items()})
    else:
        tickers = list(custom_weights.keys())
        weights = pd.Series({k: v/100 for k, v in custom_weights.items()})

    # Define the backtest period using the number of years provided via command-line argument
    end_date = datetime.datetime.today()
    start_date = end_date - datetime.timedelta(days=365 * cmd_args.years)

    # Download historical monthly closing prices for the tickers
    data = yf.download(tickers, start=start_date, end=end_date, interval="1mo")["Close"]

    # Drop months with missing price data to ensure consistent calculations
    data = data.dropna()

    # Use the last available trading day of each month
    monthly_data = data.resample('M').last()

    # Normalize each stock's price to start at 1 for fair comparison
    normalized_data = monthly_data / monthly_data.iloc[0]

    # Calculate total return for each stock
    final_prices = monthly_data.iloc[-1]
    initial_prices = monthly_data.iloc[0]
    returns = (final_prices - initial_prices) / initial_prices * 100

    # Sort columns by performance over the selected period
    sorted_columns = returns.sort_values(ascending=False).index
    normalized_data = normalized_data[sorted_columns]
    weights = weights.reindex(sorted_columns).fillna(0)

    # Calculate how much of the portfolio is unallocated (to be treated as cash)
    total_weight = weights.sum()
    cash_weight = 1.0 - total_weight if total_weight < 1.0 else 0.0

    # Normalize weights to ensure they sum to 1 after including cash
    if total_weight > 0:
        weights = weights / (weights.sum() + cash_weight)

    # Display the full weight allocation including FDRXX (cash)
    if cash_weight > 0:
        weights["FDRXX"] = cash_weight

    print("\nInitial Weights:")
    print(weights.sort_values(ascending=False).to_string())

    # Calculate the weighted portfolio value over time
    portfolio_value = (normalized_data * weights).sum(axis=1)

    # If cash is present, simulate growth at a 5% annual yield, compounded monthly
    if cash_weight > 0:
        monthly_yield = (1 + 0.05) ** (1 / 12) - 1
        months = len(portfolio_value)
        cash_growth = [(1 + monthly_yield) ** i for i in range(months)]
        cash_series = pd.Series(cash_growth, index=portfolio_value.index)

        # Add the cash component to the total portfolio value
        portfolio_value += cash_weight * cash_series

        # Add cash to normalized data and weights under the label FDRXX
        normalized_data["FDRXX"] = cash_series / cash_series.iloc[0]

    # Calculate month-over-month returns
    monthly_returns = portfolio_value.pct_change() * 100

    # Build a summary DataFrame of portfolio value and returns
    summary = pd.DataFrame({
        "Portfolio Value": portfolio_value,
        "Monthly Return (%)": monthly_returns
    })

    # Display normalized price data
    print("\nNormalized Prices (Sorted by Yearly Performance):\n", normalized_data)

    # Display the month-end summary
    print("\nMonthly Retrospective:\n", summary)

    # Recalculate total return for each stock and identify top N performers
    final_prices = normalized_data.iloc[-1]
    initial_prices = normalized_data.iloc[0]
    total_returns = (final_prices - initial_prices) / initial_prices * 100
    top_n = total_returns.sort_values(ascending=False).head(cmd_args.top)

    print(f"\nTop {cmd_args.top} Best-Performing Stocks over {cmd_args.years} Year(s):")
    print(top_n.to_string())

    # Print final portfolio return
    initial_value = portfolio_value.iloc[0]
    final_value = portfolio_value.iloc[-1]
    total_return = (final_value - initial_value) / initial_value * 100
    print(f"\nTotal Portfolio Return over {cmd_args.years} Year(s): {total_return:.2f}%")

# Entry point for script execution
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Backtest an equal or custom-weighted stock portfolio over a specified number of years.')
    parser.add_argument('--years', action="store", type=int, default=1, help='Number of years to backtest')
    parser.add_argument('--top', action="store", type=int, default=10, help='Number of top performing stocks to display')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--equalweight', nargs='+', help='List of tickers to use with equal weighting (mutually exclusive with --weighted)')
    group.add_argument('--weighted', nargs='+', help='Ticker:Weight format (e.g., AAPL:30 MSFT:70)')
    cmd_args = parser.parse_args()
    main()
    sys.exit(0)
