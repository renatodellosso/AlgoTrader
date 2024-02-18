import gc
from matplotlib import pyplot as plt
import numpy
import pandas
import yfinance
from predicting import getChange
from trading import generateBuyAndSellLists
from training import train
from stocklist import stocklist

# Returns (predictedChanges, realPrices)
def getPredictedChangesAndRealPrices( \
    symbols: list[str], timesteps: int = 40, days: int = 365 * 10, trainingRatio: float = 0.8, offsetDays: int = 0) \
    -> tuple[dict[str, list[float]], dict[str, list[float]]]:
    today = pandas.Timestamp.today()
    today = today - pandas.Timedelta(days=offsetDays)
    startDate = today - pandas.Timedelta(days=days)

    # Get predicted and real prices for each stock
    predictedChanges = {}
    realPrices = {}
    for symbol in symbols:
        print("Getting predicted prices for " + symbol + "...")

        print("Downloading data from " + startDate.strftime("%Y-%m-%d") + " to " + today.strftime("%Y-%m-%d") + "...")
        data = pandas.DataFrame(yfinance.download(symbol, start=startDate, end=today))
        print("Done!")

        trainingData = data[:int(len(data) * trainingRatio)]
        testingData = data[int(len(data) * trainingRatio) - timesteps:]

        # Be really careful with : placement here!
        model = train(trainingData, timesteps, symbol)

        # Get predictions from model
        predictedChanges[symbol] = []
        startTime = pandas.Timestamp.now()
        for i in range(timesteps, len(testingData) - 1):
            if i % 100 == 0:
                print("Predicting " + symbol + " day " + str(i - timesteps) + \
                    "/" + str(len(testingData) - timesteps) + "...")
            predictedChanges[symbol].append(getChange(model, testingData[:i], timesteps))

        # Log time stats
        timeTaken = pandas.Timestamp.now() - startTime
        print("Time to predict", symbol + ": ", timeTaken)
        timePerPrediction = timeTaken.total_seconds() / (len(testingData) - timesteps)
        print("Time per prediction:", timePerPrediction, "seconds")

        # predictedPrices[symbol] = \
        #     predictPrices(model, testingData, timesteps)

        realPrices[symbol] = data["Close"].values[len(trainingData):]

        del data, model
        gc.collect()

    return (predictedChanges, realPrices)

class TestResults:
    def __init__(self, money: float, shares: dict[str, float], netWorth: list[float], profitBySymbol: dict[str, float], \
                holdings: dict[str, list[float]]):
        self.money = money
        self.shares = shares
        self.netWorth = netWorth
        self.profitBySymbol = profitBySymbol
        self.holdings = holdings

def sellShares(sellList: dict[str, float], realPrices: dict[str, list[float]], i: int) -> None:
    global money, shares, buyPrices, profitBySymbol, wins, losses

    for symbol, shareCount in sellList.items():
        if shareCount <= 0:
            continue

        # Sell shares
        priceDiff = realPrices[symbol][i] - buyPrices[symbol]

        if priceDiff > 0:
            wins += 1
        elif priceDiff < 0:
            losses += 1

        tradeProfit = shareCount * priceDiff
        tradeValue = shareCount * realPrices[symbol][i]
        
        # Update profit by symbol
        if symbol not in profitBySymbol:
            profitBySymbol[symbol] = 0
        profitBySymbol[symbol] += tradeProfit

        # Update money and shares
        money += tradeValue
        shares[symbol] -= shareCount

def buyShares(buyList: dict[str, float], realPrices: dict[str, list[float]], i: int) -> None:
    global money, shares, buyPrices

    purchaseValue = 0
    buyingPower = money
    for symbol, shareCount in buyList.items():
        if shareCount == 0:
            continue

        if symbol not in shares:
            shares[symbol] = 0

        realPrice = realPrices[symbol][i]

        # Generate buy price by weighted average
        if shareCount + shares[symbol] == 0:
            print("Error: shareCount + shares[symbol] == 0")

        if symbol not in buyPrices or shares[symbol] == 0 or shareCount + shares[symbol] == 0:
            buyPrices[symbol] = realPrice
        else:
            buyPrices[symbol] = (realPrice * shareCount \
                + (buyPrices[symbol] * shares[symbol])) \
                / (shareCount + shares[symbol])

        sharesBought = buyList[symbol]
        shares[symbol] += sharesBought
        money -= sharesBought * realPrice
        purchaseValue += sharesBought * realPrice

    if purchaseValue - buyingPower > 1:
        print("Error: purchaseValue > buyingPower")
        print("\tpurchaseValue:", purchaseValue)
        print("\tbuyingPower:", buyingPower)
        print("\tbuyList:", buyList)
        
        # Adjust buylist by real price
        for symbol in buyList:
            buyList[symbol] *= realPrices[symbol][i]
        print("\tbuyList adjusted:", buyList)

def getTotalEquity(symbols: list[str], realPrices: dict[str, list[float]], i: int) -> float:
    global money, shares

    totalEquity = money
    for symbol in symbols:
        totalEquity += shares[symbol] * realPrices[symbol][i]
    return totalEquity

def testDay(symbols: list[str], predictedChanges: dict[str, list[float]], realPrices: dict[str, list[float]], \
    dayNum: int, i: int, timesteps: int = 40) -> None:
    global money, shares, netWorth, buyPrices, profitBySymbol, holdings

    if dayNum % 100 == 0:
        print("Day " + str(i-timesteps) + "/" + str(len(predictedChanges[symbols[0]])) + "...")

    if len(predictedChanges[symbols[0]]) <= i + 1 or len(realPrices[symbols[0]]) <= i + 1:
        return

    changes = {}
    for symbol in symbols:
        if len(predictedChanges[symbol]) <= i + 1 or len(realPrices[symbol]) <= i + 1:
            continue

        diff = predictedChanges[symbol][i]
        changes[symbol] = diff
        
    (buyList, sellList) = generateBuyAndSellLists(changes, True)

    # Convert sellList to a dict, where key is symbol and value is number of shares to sell
    sellList = {symbol: shares[symbol] if shares[symbol] > 0 else 0 for symbol in sellList}

    # Caculate total equity
    totalEquity = getTotalEquity(symbols, realPrices, i)

    # Calculate adjustment to each stock based on total equity
    for symbol in buyList:
        buyList[symbol] *= totalEquity # Convert from % of total equity to USD
        # Convert from USD to shares
        buyList[symbol] /= realPrices[symbol][i]

        # Determine adjustment
        # print(symbol, "buyList:", buyList[symbol], "shares:", shares[symbol])
        if shares[symbol] <= buyList[symbol]:
            buyList[symbol] -= shares[symbol]
        else:
            sellList[symbol] = shares[symbol] - buyList[symbol]
            buyList[symbol] = 0

    # Sell everything in sellList
    sellShares(sellList, realPrices, i)

    # Calculate money required for buyList
    moneyRequired = 0
    for symbol in buyList:
        moneyRequired += buyList[symbol] * realPrices[symbol][i]
    if moneyRequired - money > 1:
        print("Error: moneyRequired > money")
        print("\tmoneyRequired:", moneyRequired)
        print("\tmoney:", money)
        print("\tsellList:", sellList)
        print("\tbuyList:", buyList)

        print("\ttotalEquity:", totalEquity)
        shareValues = {}
        for symbol in symbols:
            shareValues[symbol] = shares[symbol] * realPrices[symbol][i]
        print("\tshareValues:", shareValues)

    # Buy shares
    buyShares(buyList, realPrices, i)

    # Calculate net worth
    netWorthToday = money
    for symbol in symbols:
        netWorthToday += shares[symbol] \
            * realPrices[symbol][i]
    netWorth.append(netWorthToday)

    # Log value of each holding
    for symbol in symbols:
        holdings[symbol].append(shares[symbol] * realPrices[symbol][i])
    holdings["Money"].append(money)

    if money < -0.1:
        input("Money is negative: " + str(money) + ". Press Enter to continue...")

def testModel(symbols: list[str], predictedChanges: dict[list[float]], realPrices: dict[list[float]], timesteps: int = 40) \
    -> TestResults:
    # Initialize variables for testing
    print("Preparing variables for testing...")

    # Declare global variables
    global money, shares, netWorth, buyPrices, profitBySymbol, holdings, wins, losses

    money = 100.0
    shares = {}

    wins = 0
    losses = 0

    for symbol in symbols:
        shares[symbol] = 0

    netWorth = []

    # Test model
    print("Testing model...")
    buyPrices = {}
    profitBySymbol = {}
    holdings = {symbol: [] for symbol in symbols}
    holdings["Money"] = []

    startTime = pandas.Timestamp.now()
    for i in range(0, len(predictedChanges[symbols[0]]) - 1):
        dayNum = i - timesteps
        testDay(symbols, predictedChanges, realPrices, dayNum, i, timesteps)

    # Log time stats
    endTime = pandas.Timestamp.now()
    timeTaken = endTime - startTime
    print("Time to test:", timeTaken)
    timePerDay = timeTaken.total_seconds() / (len(predictedChanges[symbols[0]]) - timesteps)
    print("Time per day:", timePerDay, "seconds")

    # Sell all shares
    for symbol in symbols:
        if symbol in buyPrices:
            # Calculate profit from this trade
            tradeProfit = shares[symbol] * (realPrices[symbol][-1] - buyPrices[symbol])
            if symbol not in profitBySymbol:
                profitBySymbol[symbol] = 0
            profitBySymbol[symbol] += tradeProfit
        print("Selling", shares[symbol], "shares of", symbol, "for", realPrices[symbol][-1] * shares[symbol], \
            "USD - Profit:", tradeProfit, "USD")
        money += shares[symbol] * realPrices[symbol][-1]
        shares[symbol] = 0

    return TestResults(money, shares, netWorth, profitBySymbol, holdings)

def graphMultiStockTest(results: TestResults, days: int, realPrices: dict[str, list[float]]) -> None:
    # Plot results
    print("Plotting results...")

    # dict.values() returns a view, so we need to convert it to a list
    # [*dict] unpacks the view
    stackAxis = numpy.vstack([*results.holdings.values()])
 
    fig, axis = plt.subplots()

    axis.stackplot(range(len(results.netWorth)), stackAxis, labels=results.holdings.keys())
    axis.plot([100] * len(results.netWorth), color='black', label='Starting Net Worth')
    axis.plot([0] * len(results.netWorth), color='red')

    # Fetch S&P 500 data and add it to the plot
    # today = pandas.Timestamp.today()
    # startDate = today - pandas.Timedelta(days=days)
    # sp500 = yfinance.download( \
    #     '^GSPC', start=startDate, end=today)
    # print(days)
    # print(len(sp500["Close"].values))
    # print(len(results.netWorth))
    # axis.plot(sp500["Close"].values / sp500["Close"].values[0] * 100, color='green', label='S&P 500')

    # Plot real prices
    for symbol, prices in realPrices.items():
        prices = prices[:len(results.netWorth)]
        axis.plot(prices / prices[0] * 100, label=symbol)

    plt.title('Algo Trade Test Results')
    plt.xlabel('Time')
    plt.ylabel('Net Worth')
    plt.legend()
    plt.show()

def testMultiStock(symbols: list[str], timesteps: int = 40, days: int = 365 * 10, trainingRatio: float = 0.8, offsetDays: int = 0, \
        trainingDays: int = 0) -> None:
    overallStartTime = pandas.Timestamp.now()

    if trainingDays > 0:
        # Convert from trainingDays to trainingRatio
        trainingRatio = trainingDays / days
    
    # Get predicted and real prices for each stock
    (predictedChanges, realPrices) = \
        getPredictedChangesAndRealPrices(symbols, timesteps, days, trainingRatio, offsetDays)
    
    # Test model
    testResults = testModel(symbols, predictedChanges, realPrices, timesteps)

    # Calculate % profit and annualized return
    profit = testResults.money - 100
    profitPercent = profit / 100

    days = len(predictedChanges[symbols[0]])
    years = days / 365
    annualizedReturn = (1 + profitPercent) ** (1 / years) - 1

    print("Days Elapsed:", days)
    print("Years Elapsed:", years)
    print("Shares:", testResults.shares)
    print("Money:", testResults.money)
    print("Profit:", round(profit, 2))
    print("Profit %:", round(profitPercent * 100, 2))
    print("Annualized Return %:", round(annualizedReturn * 100, 2))

    # Calculate win rate
    totalTrades = wins + losses
    print("Win Rate:", wins, "/", totalTrades, "=", str(round(wins / totalTrades, 3) * 100) + "%")

    # Log profit by symbol
    print("Profit by Symbol:")
    for symbol in symbols:
        print(symbol + " Profit:", testResults.profitBySymbol[symbol] if symbol in testResults.profitBySymbol else "0", \
            "(% of total profit: " + str(round(testResults.profitBySymbol[symbol] / profit * 100, 2)) + "%)")

    # Log time stats
    overallTimeTaken = pandas.Timestamp.now() - overallStartTime
    print("Overall Time:", overallTimeTaken)
    timePerDay = overallTimeTaken.total_seconds() / (len(predictedChanges[symbols[0]]) - timesteps)
    print("Overall Time per Day:", timePerDay, "seconds")

    graphMultiStockTest(testResults, days, realPrices)

if __name__ == "__main__":
    # testMultiStock(stocklist, days=365*20, trainingDays=365*8)
    testMultiStock(["BAC", "INTC"], days=365*10, trainingDays=365*5, timesteps=20)

# Testing done on 2/18/24

# 5 years of training, 5 years of testing

# 3 years of training, 3 years of testing 
# Timesteps: Annualized Return
# 20: -6.21, -17.74
# 10: -13.68, -9.59
# 5: -14.61, -15.46

# 1 year of training, 1 year of testing
# Timesteps: Annualized Return
# 40: 4.88, 3.29
# 30: 19.96, 11.74, 9.84
# 20: 7.01, 16.42, 24.5
# 10: 17.96, 20.78, 34.09
# 5: 14.89, 17.67, 11.88