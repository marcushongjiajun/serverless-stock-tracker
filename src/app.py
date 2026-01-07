import yfinance as yf
import pandas as pd

# Wallstreetbets top picks for 2026 + Personal speculation plays
watchlist = ["ASTS", "RKLB", "GOOG", "AMZN", "NBIS", "RDDT", "MU", "IREN", "TSLA", "PLTR", "AVAV", "D05.SI", "O39.SI"]
results = []

for ticker_symbol in watchlist:
    try:
        stock = yf.Ticker(ticker_symbol)
        # Pull two years to ensure there is enough data for 200-day average
        df = stock.history(period="2y")

        # Obtain fundamental data from .info
        info = stock.info
        company_name = info.get('longName', 'Unknown')
        short_name = (company_name[:23] + '..') if len(company_name) > 23 else company_name
        forward_pe_ratio = info.get('forwardPE') # get.() is used to avoid errors if PE is missing

        # Calculate Moving Averages
        df['SMA50'] = df['Close'].rolling(window=50).mean()
        df['SMA200'] = df['Close'].rolling(window=200).mean()

        # Get today and yesterday's values, for comparison
        last_price = df['Close'].iloc[-1]
        last_date = df.index[-1].strftime("%Y-%m-%d")
        today_sma50 = df["SMA50"].iloc[-1]
        today_sma200 = df["SMA200"].iloc[-1]
        yesterday_sma50 = df["SMA50"].iloc[-2]
        yesterday_sma200 = df["SMA200"].iloc[-2]

        # Golden Cross Logic: Define the status
        today_is_golden = today_sma50 > today_sma200
        yesterday_was_golden = yesterday_sma50 > yesterday_sma200

        if today_is_golden and not yesterday_was_golden:
            signal = "🚀 BUY SIGNAL (Golden Cross Today!)"
        elif not today_is_golden and yesterday_was_golden:
            signal = "⚠️ SELL SIGNAL (Death Cross Today!)"
        else:
            # Same state as yesterday
            status = "Bullish" if today_is_golden else "Bearish"
            signal = f"No Change ({status})"

        # PE Ratio: determine how "expensive" a stock is
        if forward_pe_ratio is None or forward_pe_ratio <= 0:
            # If P/E is negative or zero, its not "cheap", its "loss-making"
            valuation = "N/A (Loss Making)"
        elif forward_pe_ratio < 15:
            valuation = "Value (Cheap)"
        elif 15 <= forward_pe_ratio <= 30:
            valuation = "Fair"
        else:
            valuation = "Expensive (Growth)"


        results.append({
            "Ticker": ticker_symbol,
            "Name": short_name,
            "Date": last_date,
            "Price": round(last_price, 2),
            "Status": status,
            "Golden Cross Signal": signal,
            "Forward P/E": round(forward_pe_ratio, 2) if forward_pe_ratio else "N/A",
            "Valuation": valuation
        })
    
    except Exception as e:
        print(f"Error on {ticker_symbol}: {e}")


summary_df = pd.DataFrame(results)
valuation_order = ["Value (Cheap)", "Fair", "Expensive (Growth)", "N/A (Loss Making)"]
summary_df['Valuation'] = pd.Categorical(summary_df['Valuation'], categories=valuation_order, ordered=True)
summary_df = summary_df.sort_values('Valuation')

print("\n------------------------------- Stock Analysis -------------------------------")
print(summary_df.to_string(index=False))

