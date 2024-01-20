import datetime
import gc
import platform
import time
from pandas import DataFrame
import pandas
import yfinance
import concurrent.futures

from api import getBalance, getPosition, placeBuyOrder, placeSellOrder
from sheets import log
from testing import predictToday, predictTomorrow
from training import train

symbols = ["KO", "CVX", "PM", "INTC", "WFC", "BAC"]
days = 365 * 10 # 10 years works well

def startLoop() ->  None:
    log("Starting trading loop...")
    try:
        while True:
            # Check if time is between 9:30AM and 4PM
            now = datetime.datetime.now()

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
                now = datetime.datetime.now()
                while(now.hour < 16):
                    time.sleep(3600)
                    now = datetime.datetime.now()
            
            # Sleep for 1 hour
            log("Sleeping for 1 hour...")
            time.sleep(3600)
    except KeyboardInterrupt:
        log("Keyboard Interrupt!")
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
            log("Error Predicting Symbol (" + symbol + "):", e)
            expectedChanges[symbol] = 0
    endTime = datetime.datetime.now()

    timeTaken = endTime - startTime
    log("Finished predicting symbols! Time taken: " + str(timeTaken))

    log("Expected changes:" + str(expectedChanges))

    # Sell symbols where expected change is < 0
    for symbol in symbols:
        if expectedChanges[symbol] < 0:
            # Sell
            shares = getPosition(symbol)
            if shares > 0:
                print("Selling" + str(shares) + "shares of" + symbol + "...")
                placeSellOrder(symbol, shares)

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

    # Wait for a few minutes to allow sell orders to complete
    log("Waiting for a few minutes to allow sell orders to be processed...")
    time.sleep(60 * 10)

    # Buy symbols where expected change is > 0
    balance = getBalance()
    log("Balance:", balance)
    for symbol in expectedChanges:
        # Buy
        if balance > 0:
            shares = balance * expectedChanges[symbol] / yfinance.Ticker(symbol).info['regularMarketOpen']
            shares = shares[0] # Not sure how it's ending up as an array
            log("Buying " + str(shares) + " shares of " + (symbol) + "...")
            placeBuyOrder(symbol, shares)

def getExpectedChange(symbol: str) -> float:
    log("Getting expected change for " + symbol + "...")
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=1) as executor:
        log("Starting getPredictedPrices function on other process...")
        process = executor.submit(getPredictedPrices, symbol)
        log("Waiting for getPredictedPrices function to finish...")

        exception = process.exception()
        if exception != None:
            raise exception
        predictions = process.result()

    if predictions == None:
        log("Predictions is None!")
        return 0

    # Get today's price
    todayPrice = predictions[0]

    # Get predicted prices
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

        # Get data
        data = getData(symbol)

        # Train model
        log("Training model for " + symbol + "...")
        model = train(data, 40)

        if(model == None):
            log("Model is None!")
            del data
            del model
            gc.collect()
            return 0

        log("Done!")

        # Get today's price
        todayPrice = data.iloc[-1]['Close']

        # Get predicted prices
        predictedPriceToday = predictToday(model, data, 40)
        predictedPriceTmr = predictTomorrow(model, data, 40)

        # Delete unneeded variables to free up ram
        del model
        del data
        gc.collect()

        return (todayPrice, predictedPriceToday, predictedPriceTmr)
    except Exception as e:
        log("Error getting predicted prices for " + symbol + ":", e)
        return None