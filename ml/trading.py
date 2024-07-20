import datetime
import gc
import platform
import time
from pandas import DataFrame
import pandas
import yfinance
from numpy import float64

import sys
sys.path.append('../AlgoTrader')
from api import getEquity, getOpenOrders, getPosition, placeBuyOrder, placeSellOrder, tradingClient
from sheets import log, logTransaction
from predicting import getChange, getChangeTuple, predictPrices
from training import train
from stocklist import stocklist
from exitflag import exitFlag

symbols = stocklist
days = 365 * 10 # 10 years works well
timesteps = 40

est = datetime.timezone(datetime.timedelta(hours=-5))

def keyboardExit():
    log("Keyboard Interrupt!")
    global exitFlag
    exitFlag.set()
    time.sleep(5)
    exit()

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
        keyboardExit()
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

    (buyList, sellList) = generateBuyAndSellLists(expectedChanges)

    # Key: symbol, Value: shares
    sellOrders = {}

    # Sell symbols where expected change is < 0
    for symbol in sellList:
            # Sell
        shares = getPosition(symbol)
        if shares > 0:
            sellOrders[symbol] = shares

    # Compute target # of shares
    equity = getEquity()
    buyOrders = {} # Key: symbol, Value: shares
    for symbol, percentage in buyList.items():
        targetValue = percentage * equity

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

    diff = getPredictedChange(symbol)

    if diff == None:
        log("Difference is None!")
        return 0
    
    log("Difference: " + str(diff))

    return diff

def getPredictedChange(symbol: str) -> float | None:
    try:
        log("Getting predicted prices for " + symbol + "...")

        # Get data, repeat until data is defined
        while not 'data' in locals():
            try:
                data = getData(symbol)
            except KeyboardInterrupt:
                keyboardExit()
            except Exception as e:
                log("Error downloading data for " + symbol + ": " + str(e))
                time.sleep(60)

        # Train model
        log("Training model for " + symbol + "...")
        model = train(data, timesteps, symbol)

        if(model == None):
            log("Model is None!")
            del data, model
            gc.collect()
            return 0

        log("Done!")

        # Get predicted prices
        diff = getChange(model, data[int(len(data) * 0.8):], timesteps)

        # Delete unneeded variables to free up ram
        del model, data
        gc.collect()

        return diff
    except KeyboardInterrupt:
        keyboardExit()
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

# Returns (buyList, sellList). Buylist is a dict with symbols as keys and percentage as values. SellList is a list of symbols
def generateBuyAndSellLists(changes: dict, testingMode: bool = False) -> tuple[dict, list[str]]:
    sellList = []
    buyList = {}

    # Sell symbols where expected change is < 0 and add others to buy list
    for symbol in changes:
        if changes[symbol] < 0:
            # Sell
            proceed = testingMode or getPosition(symbol) > 0
            if proceed:
                sellList.append(symbol)
        else:
            # Buy
            buyList[symbol] = float64(changes[symbol])

    # Convert buylist into a percentage of total
    total = sum(buyList.values())

    for symbol in buyList:
        # print(type(buyList[symbol]), type(total))
        if total != 0:
            buyList[symbol] = buyList[symbol] / total
        else:
            buyList[symbol] = 0

    return (buyList, sellList)