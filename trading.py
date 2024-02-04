import datetime
import gc
import platform
import time
from pandas import DataFrame
import pandas
import yfinance
import concurrent.futures

from api import getBuyingPower, getEquity, getOpenOrders, getPosition, placeBuyOrder, placeSellOrder, tradingClient
from sheets import log, logTransaction
from predicting import predictPrices
from training import train
from stocklist import stocklist

symbols = stocklist
days = 365 * 10 # 10 years works well

est = datetime.timezone(datetime.timedelta(hours=-5))

def startLoop() ->  None:
    log("Starting trading loop...")
    try:
        while True:
            # Check if time is between 9:30AM and 4PM
            now = datetime.datetime.now(est)

            hasRanLoop = False
            if(now.hour >= 9 and now.hour < 16) or platform.system() == "Windows" or not hasRanLoop:
                
                # Run trading loop
                log("Running trading loop...")
                try:
                    dailyTrade()
                except Exception as e:
                    log("Error in Daily Trade Loop:" + str(e))
                log("Done!")

                hasRanLoop = True

                # Sleep until after 4 PM
                log("Sleeping until after 4 PM...")
                now = datetime.datetime.now(est)
                while(now.hour < 16):
                    time.sleep(3600)
                    now = datetime.datetime.now(est)
            
            # Sleep for 1 hour
            log("Sleeping for 1 hour...")
            time.sleep(3600)
    except KeyboardInterrupt:
        log("Keyboard Interrupt!")
        exit()
    except Exception as e:
        log("Error:" + str(e))
    finally:
        log("Trading loop stopped!")
        # exit()

def getData(symbol: str) -> DataFrame:
    # Get historical data
    today = pandas.Timestamp.today()
    start_date = today - pandas.Timedelta(days=days)

    log("Downloading data from " + start_date.strftime("%Y-%m-%d") + " to " + today.strftime("%Y-%m-%d") + "...")
    data = pandas.DataFrame(yfinance.download(symbol, start=start_date, end=today))
    log("Done!")

    return data

def dailyTrade() -> None:
    expectedChanges = {}

    # Get expected changes for each symbol
    startTime = datetime.datetime.now()
    for symbol in symbols:
        try:
            expectedChanges[symbol] = getExpectedChange(symbol)
        except Exception as e:
            log("Error Predicting Symbol (" + symbol + "):" + str(e))
            expectedChanges[symbol] = 0
    endTime = datetime.datetime.now()

    timeTaken = endTime - startTime
    log("Finished predicting symbols! Time taken: " + str(timeTaken))

    log("Expected changes:" + str(expectedChanges))

    cancelOpenOrders()

    # Key: symbol, Value: shares
    sellOrders = {}

    # Sell symbols where expected change is < 0
    for symbol in symbols:
        if expectedChanges[symbol] < 0:
            # Sell
            shares = getPosition(symbol)
            if shares > 0:
                sellOrders[symbol] = shares

    # Remove symbols where expected change is < 0 from expectedChanges
    for symbol in symbols:
        if expectedChanges[symbol] < 0:
            expectedChanges.pop(symbol)

    # Calculate total expected change
    totalExpectedChange = 0
    for symbol in expectedChanges:
        totalExpectedChange += expectedChanges[symbol]

    # Convert expected changes to percentages of total
    for symbol in expectedChanges:
        expectedChanges[symbol] = expectedChanges[symbol] / totalExpectedChange

    log("Expected changes (% of total): " + str(expectedChanges))

    # Compute target # of shares
    equity = getEquity()
    buyOrders = {} # Key: symbol, Value: shares
    for symbol in expectedChanges:
        targetValue = expectedChanges[symbol][0] * equity

        # Get current price
        price = yfinance.Ticker(symbol).info['bid']
        targetShares = targetValue / price

        # Determine adjustment
        currentShares = getPosition(symbol)
        adjustment = targetShares - currentShares

        print("Target value for " + symbol + ": $" + str(round(targetValue, 2)))
        print("Target shares for " + symbol + ": " + str(round(targetShares, 2)))
        print("Current shares for " + symbol + ": " + str(round(currentShares, 2)))
        print("Adjustment for " + symbol + ": " + str(round(adjustment, 2)))

        if adjustment < 0:
            # Sell
            sellOrders[symbol] = -adjustment
        else:
            # Buy
            buyOrders[symbol] = adjustment

    # Log orders
    log("Sell Orders:" + str(sellOrders))
    log("Buy Orders:" + str(buyOrders))

    # Place sell orders
    for symbol in sellOrders:
        log("Selling " + str(sellOrders[symbol]) + " shares of " + symbol + "...")
        placeSellOrder(symbol, sellOrders[symbol])

    # Wait for a few minutes to allow sell orders to complete
    log("Waiting for 10 minutes to allow sell orders to be processed...")
    for i in range(10):
        time.sleep(60)
        print("Time remaining: " + str(10 - i) + " minutes...")

    # Place buy orders
    for symbol in buyOrders:
        log("Buying " + str(buyOrders[symbol]) + " shares of " + symbol + "...")
        placeBuyOrder(symbol, buyOrders[symbol])

def getExpectedChange(symbol: str) -> float:
    log("Getting expected change for " + symbol + "...")
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=1) as executor:
        print("Starting getPredictedPrices function on other process...")
        process = executor.submit(getPredictedPrices, symbol)
        print("Waiting for getPredictedPrices function to finish...")

        exception = process.exception()
        if exception != None: 
            raise exception
        predictions = process.result()

        del process
        gc.collect()

    if predictions == None:
        log("Predictions is None!")
        return 0

    # Get today's price
    todayPrice = predictions[0]

    # Get predicted prices
    # If actual performance is lower than in backtesting, try using the last 20% of data instead of the last 40 days
    predictedPriceToday = predictions[1]
    predictedPriceTmr = predictions[2]

    log("Today's price: " + str(todayPrice))
    log("Predicted price for today: " + str(predictedPriceToday))
    log("Predicted price for tomorrow: " + str(predictedPriceTmr))

    # Calculate difference
    difference = predictedPriceTmr - predictedPriceToday
    log("Difference: " + str(difference))

    return difference / predictedPriceToday

def getPredictedPrices(*args: any) -> tuple | None:
    print("getPredictedPrices function running on other process...")
    try:
        symbol = args[0]

        log("Getting predicted prices for " + symbol + "...")

        # Get data, repeat until data is defined
        while not 'data' in locals():
            try:
                data = getData(symbol)
            except KeyboardInterrupt:
                log("Keyboard Interrupt!")
                exit()
            except Exception as e:
                log("Error downloading data for " + symbol + ": " + str(e))
                time.sleep(60)

        # Train model
        log("Training model for " + symbol + "...")
        model = train(data, 40, symbol)

        if(model == None):
            log("Model is None!")
            del data, model
            gc.collect()
            return 0

        log("Done!")

        # Get today's price
        todayPrice = data.iloc[-1]['Close']

        # Get predicted prices
        predictedPrices = predictPrices(model, data[int(len(data)*0.8):], 40)
        predictedPriceToday = predictedPrices[-2] # It's possible this is actually yesterday's price
        predictedPriceTmr = predictedPrices[-1] # Might be today's price
        # predictedPriceToday = predictToday(model, data, 40)
        # predictedPriceTmr = predictTomorrow(model, data, 40)

        # Delete unneeded variables to free up ram
        del model, data
        gc.collect()

        return (todayPrice, predictedPriceToday, predictedPriceTmr)
    except KeyboardInterrupt:
        log("Keyboard Interrupt!")
        exit()
    except Exception as e:
        log("Error getting predicted prices for " + symbol + ": " + str(e))
        return None
    
def cancelOpenOrders() -> None:
    log("Cancelling all open orders...")
    openOrders = getOpenOrders()
    for order in openOrders:
        # Only cancel orders for symbols we are tracking
        if order.symbol in symbols:
            tradingClient.cancel_order_by_id(order.id)
            logTransaction(order.symbol, order.id, "CANCEL-" + order.side, order.qty, order.filled_avg_price)    