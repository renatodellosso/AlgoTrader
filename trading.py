import datetime
import time

from pandas import DataFrame
import pandas
import yfinance
from api import getBalance, getPosition, placeBuyOrder, placeSellOrder
from sheets import log
from testing import predictToday, predictTomorrow

from training import train

symbols = ["KO", "CVX", "PM", "INTC", "WFC", "BAC"]
days = 365 * 10 # 10 years works well

def startLoop() ->  None:
    log("Starting trading loop...")
    while True:
        # Check if time is between 9:30AM and 4PM
        now = datetime.datetime.now()

        if(now.hour >= 9 and now.hour < 16):
            # Run trading loop
            log("Running trading loop...")
            dailyTrade()
            log("Done!")

            # Sleep until after 4 PM
            log("Sleeping until after 4 PM...")
            now = datetime.datetime.now()
            while(now.hour < 16):
                time.sleep(3600)
                now = datetime.datetime.now()
        
        # Sleep for 1 hour
        log("Sleeping for 1 hour...")
        time.sleep(3600)

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

    for symbol in symbols:
        expectedChanges[symbol] = getExpectedChange(symbol)

    log("Expected changes:", expectedChanges)

    # Sell symbols where expected change is < 0
    for symbol in symbols:
        if expectedChanges[symbol] < 0:
            # Sell
            shares = getPosition(symbol)
            if shares > 0:
                print("Selling", shares, "shares of", symbol, "...")
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

    log("Expected changes (% of total):", expectedChanges)

    # Wait for a few minutes to allow sell orders to complete
    log("Waiting for a few minutes...")
    time.sleep(60 * 10)

    # Buy symbols where expected change is > 0
    balance = getBalance()
    log("Balance:", balance)
    for symbol in expectedChanges:
        # Buy
        if balance > 0:
            shares = balance * expectedChanges[symbol] / yfinance.Ticker(symbol).info['regularMarketOpen']
            shares = shares[0] # Not sure how it's ending up as an array
            log("Buying", shares, "shares of", symbol, ".. .")
            placeBuyOrder(symbol, shares)

def getExpectedChange(symbol: str) -> float:
    # Get data
    data = getData(symbol)

    # Get actual price for today
    todayPrice = data.iloc[-1]['Close']

    # Train model
    log("Training model for " + symbol + "...")
    model = train(data, 40)
    log("Done!")

    # Get predicted prices
    predictedPriceToday = predictToday(model, data, 40)
    predictedPriceTmr = predictTomorrow(model, data, 40)

    # Delete unneeded variables to free up ram
    del model
    del data

    log("Today's price:", todayPrice)
    del todayPrice
    log("Predicted price for today:", predictedPriceToday)
    log("Predicted price for tomorrow:", predictedPriceTmr)

    # Calculate difference
    difference = predictedPriceTmr - predictedPriceToday
    log("Difference:", difference)

    return difference / predictedPriceToday