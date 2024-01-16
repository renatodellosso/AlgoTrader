import datetime
import time

from pandas import DataFrame
import pandas
import yfinance
from api import getBalance, getPosition, placeBuyOrder, placeSellOrder
from testing import predictTomorrow

from training import train

def startLoop() ->  None:
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
    days = 365 * 10 # 10 years works well
    
    # Get historical data
    today = pandas.Timestamp.today()
    start_date = today - pandas.Timedelta(days=days)

    print("Downloading data from " + start_date.strftime("%Y-%m-%d") + " to " + today.strftime("%Y-%m-%d") + "...")
    data = pandas.DataFrame(yfinance.download(symbol, start=start_date, end=today))
    print("Done!")

    print("Data length: " + str(len(data)))

    return data

def dailyTrade() -> None:
    print("Starting daily trade...")

    symbol = "BAC" # Symbols with 20% - 30% returns over 5Y seem to work best, such as KO, CVX, PM, BAC (v. well!), INTC, WFC (v. well!)

    # Get data
    data = getData(symbol)

    # Get actual price for today
    todayPrice = data.iloc[-1]['Close']

    # Train model
    model = train(data, 40)

    # Get predicted price for tomorrow
    predictedPrice = predictTomorrow(model, data, 40)
    print("Today's price:", todayPrice)
    print("Predicted price:", predictedPrice)

    # Calculate difference
    difference = predictedPrice - todayPrice
    print("Difference:", difference)

    # Get account balance and position
    balance = getBalance()
    print("Balance:", balance)
    position = getPosition(symbol)
    print("Position:", position)

    # If difference is positive, buy
    if(balance > 0 and difference > 0):
        # Buy
        shares = int(balance / todayPrice)
        print("Buying", shares, "shares...")
        placeBuyOrder(symbol, shares)
    # If difference is negative, sell
    elif(position > 0 and difference < 0):
        # Sell
        shares = position
        print("Selling", shares, "shares...")
        placeSellOrder(symbol, shares)
    else:
        print("Holding.")

