import yfinance as yf
import pandas as pd
import boto3
import os
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    # Wallstreetbets top picks for 2026 + Personal speculation plays
    watchlist = ["ASTS", "RKLB", "GOOG", "AMZN", "NBIS", "RDDT", "MU", "IREN", "TSLA", "PLTR", "AVAV", "D05.SI", "O39.SI"]
    results = []

    logger.info(f"Starting analysis for {len(watchlist)} tickers.")

    for ticker_symbol in watchlist:
        try:
            stock = yf.Ticker(ticker_symbol)
            # Pull two years to ensure there is enough data for 200-day average
            df = stock.history(period="2y")

            if df.empty:
                logger.warning(f"No data found for {ticker_symbol}")
                continue

            # Obtain fundamental data from .info
            info = stock.info
            company_name = info.get('longName', 'Unknown')
            short_name = (company_name[:23] + '..') if len(company_name) > 23 else company_name
            forward_pe_ratio = info.get('forwardPE') # get.() is used to avoid errors if PE is missing

            # Calculate Moving Averages
            df['SMA50'] = df['Close'].rolling(window=50).mean()
            df['SMA200'] = df['Close'].rolling(window=200).mean()

            last_price = df['Close'].iloc[-1]
            last_date = df.index[-1].strftime("%Y-%m-%d")

            # Get today and yesterday's values, for comparison
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
            logger.error(f"Error processing {ticker_symbol}: {str(e)}")

    # Create and sort DataFrame
    summary_df = pd.DataFrame(results)
    valuation_order = ["Value (Cheap)", "Fair", "Expensive (Growth)", "N/A (Loss Making)"]
    summary_df['Valuation'] = pd.Categorical(summary_df['Valuation'], categories=valuation_order, ordered=True)
    summary_df = summary_df.sort_values('Valuation')

    # Prepare Message
    table_str = "📈 Daily Market Intelligence Report\n"
    table_str += "========================================\n"
    table_str += summary_df.to_string(index=False)

    # AWS SNS Integration
    sns = boto3.client('sns')
    topic_arn = os.environ.get('SNS_TOPIC_ARN')

    try:
        sns.publish(
            TopicArn=topic_arn,
            Subject=f"Stock Report: {pd.Timestamp.now().strftime('%Y-%m-%d')}",
            Message=table_str
        )
        logger.info("Report successfully published to SNS.")
        return {"statusCode": 200, "body": "Report Sent Successfully"}
    except Exception as e:
        logger.error(f"SNS Publish Failed: {str(e)}")
        return {"statusCode": 500, "body": "Failed to send report"}