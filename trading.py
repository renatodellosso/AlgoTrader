import datetime
import time

from pandas import DataFrame
import pandas
import yfinance
from api import getBalance, getPosition, placeBuyOrder, placeSellOrder
from testing import predictToday, predictTomorrow

from training import train

symbols = ["KO", "CVX", "PM", "INTC", "WFC", "BAC"]
days = 365 * 10 # 10 years works well

def startLoop() ->  None:
    print("Starting trading loop...")
    while True:
        # Check if time is between 9:30AM and 4PM
        now = datetime.datetime.now()

        if(now.hour >= 9 and now.hour < 16):
            # Run trading loop
            print("Running trading loop...")
            dailyTrade()
            print("Done!")

            # Sleep until after 4 PM
            print("Sleeping until after 4 PM...")
            now = datetime.datetime.now()
            while(now.hour < 16):
                time.sleep(3600)
                now = datetime.datetime.now()
        
        # Sleep for 1 hour
        print("Sleeping for 1 hour...")
        time.sleep(3600)

def getData(symbol: str) -> DataFrame:    
    # Get historical data
    today = pandas.Timestamp.today()
    start_date = today - pandas.Timedelta(days=days)

    print("Downloading data from " + start_date.strftime("%Y-%m-%d") + " to " + today.strftime("%Y-%m-%d") + "...")
    data = pandas.DataFrame(yfinance.download(symbol, start=start_date, end=today))
    print("Done!")

    print("Data length: " + str(len(data)))

    return data

def dailyTrade() -> None:
    expectedChanges = {}

    for symbol in symbols:
        expectedChanges[symbol] = getExpectedChange(symbol)

    print("Expected changes:")
    print(expectedChanges)

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

    print("Expected changes (% of total):")
    print(expectedChanges)

    # Buy symbols where expected change is > 0
    balance = getBalance()
    print("Balance:", balance)
    for symbol in expectedChanges:
        # Buy
        if balance > 0:
            shares = balance * expectedChanges[symbol] / yfinance.Ticker(symbol).info['regularMarketOpen']
            shares = shares[0] # Not sure how it's ending up as an array
            print("Buying", shares, "shares of", symbol, ".. .")
            placeBuyOrder(symbol, shares)

def getExpectedChange(symbol: str) -> float:
    # Get data
    data = getData(symbol)

    # Get actual price for today
    todayPrice = data.iloc[-1]['Close']

    # Train model
    print("Training model for " + symbol + "...")
    model = train(data, 40)

    # Get predicted prices
    predictedPriceToday = predictToday(model, data, 40)
    predictedPriceTmr = predictTomorrow(model, data, 40)
    print("Today's price:", todayPrice)
    print("Predicted price for today:", predictedPriceToday)
    print("Predicted price for tomorrow:", predictedPriceTmr)

    # Calculate difference
    difference = predictedPriceTmr - predictedPriceToday
    print("Difference:", difference)

    return difference / predictedPriceToday