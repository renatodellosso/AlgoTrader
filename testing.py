import gc
import numpy
import pandas
from keras import Sequential
from sklearn.preprocessing import MinMaxScaler
import yfinance
from graphing import graphMultiStockTest, graphTest
from training import train

def predictToday(model: Sequential, data: pandas.DataFrame, timesteps: int = 40) -> float:
    datasetTotal = data["Close"]
    inputs = datasetTotal.values

    inputs = inputs.reshape(-1, 1) # param1 is number of rows, param2 is size of each row
    scaler = MinMaxScaler(feature_range=(0, 1))
    inputs = scaler.fit_transform(inputs)

    xTest = [inputs[-timesteps-1:-1]]

    xTest = numpy.array(xTest)
    xTest = numpy.reshape(xTest, (xTest.shape[0], xTest.shape[1], 1))

    # xTest is a 3D array

    # Predict
    print("Predicting...")  
    predictedPrice = model.predict(xTest)
    predictedPrice = scaler.inverse_transform(predictedPrice)

    return predictedPrice[-1]

def predictTomorrow(model: Sequential, data: pandas.DataFrame, timesteps: int = 40) -> float:
    datasetTotal = data["Close"]
    inputs = datasetTotal.values

    inputs = inputs.reshape(-1, 1) # param1 is number of rows, param2 is size of each row
    scaler = MinMaxScaler(feature_range=(0, 1))
    inputs = scaler.fit_transform(inputs)

    xTest = [inputs[-timesteps:]]

    xTest = numpy.array(xTest)
    xTest = numpy.reshape(xTest, (xTest.shape[0], xTest.shape[1], 1))

    # xTest is a 3D array

    # Predict
    print("Predicting...")  
    predictedPrice = model.predict(xTest)
    predictedPrice = scaler.inverse_transform(predictedPrice)

    return predictedPrice[-1]

def predictPrices(model: Sequential, data: pandas.DataFrame, timesteps: int = 40) -> numpy.ndarray:
    datasetTotal = data["Close"]
    inputs = datasetTotal.values

    inputs = inputs.reshape(-1, 1) # param1 is number of rows, param2 is size of each row
    scaler = MinMaxScaler(feature_range=(0, 1))
    inputs = scaler.fit_transform(inputs)

    xTest = [[0] * timesteps] * timesteps
    for i in range(timesteps, len(inputs)):
        xTest.append(inputs[i - timesteps:i, 0])

    xTest = numpy.array(xTest)
    xTest = numpy.reshape(xTest, (xTest.shape[0], xTest.shape[1], 1))

    # xTest is a 3D array

    # Predict
    print("Predicting...")  
    predictedPrice = model.predict(xTest)
    predictedPrice = scaler.inverse_transform(predictedPrice)

    return predictedPrice

def test(model: Sequential, data: pandas.DataFrame, timesteps: int = 40) -> None:
    print("Preparing to test model... Data Length: " + str(len(data)))
    realPrice = data.iloc[:, 1:2].values
    datasetTotal = data["Close"]
    inputs = datasetTotal.values

    inputs = inputs.reshape(-1, 1) # param1 is number of rows, param2 is size of each row
    scaler = MinMaxScaler(feature_range=(0, 1))
    inputs = scaler.fit_transform(inputs)

    xTest = [[0] * timesteps] * timesteps
    for i in range(timesteps, len(inputs)):
        xTest.append(inputs[i - timesteps:i, 0])

    xTest = numpy.array(xTest)
    xTest = numpy.reshape(xTest, (xTest.shape[0], xTest.shape[1], 1))

    # xTest is a 3D array

    # Predict
    print("Predicting...")  
    predictedPrice = model.predict(xTest)
    predictedPrice = scaler.inverse_transform(predictedPrice)

    algoTrade(predictedPrice, realPrice, timesteps)

def algoTrade(predictedPrices: numpy.ndarray, realPrices: numpy.ndarray, timesteps: int) -> None:
    # Convert predictedPrices and realPrices to 1D arrays
    predictedPrices = predictedPrices.flatten()
    realPrices = realPrices.flatten()

    money = realPrices[timesteps - 1]
    print("Starting Money: " + str(money))
    shares = 0

    actionsX = []
    actionsY = []
    actionsC = []
    netWorth = []
    for i in range(timesteps, len(predictedPrices) - 1):
        netWorth.append(money + shares * realPrices[i])
        if money > 0 and predictedPrices[i] < predictedPrices[i + 1]:
            # Buy
            shares = money / realPrices[i]
            money = 0
            actionsX.append(i - timesteps)
            actionsY.append(realPrices[i])
            actionsC.append('green')
            i += 2 # Trades take 2 days to complete
        elif shares > 0 and predictedPrices[i] > predictedPrices[i + 1]:
            # Sell
            money = shares * realPrices[i]
            shares = 0
            actionsX.append(i - timesteps)
            actionsY.append(realPrices[i])
            actionsC.append('red')
            i += 2 # Trades take 2 days to complete

    money += shares * realPrices[-1]
    netWorth.append(money)
    shares = 0

    # Calculate % profit for both our trades and just holding
    profit = (money - realPrices[timesteps - 1]) / realPrices[timesteps - 1]
    holdProfit = (realPrices[-1] - realPrices[timesteps - 1]) / realPrices[timesteps - 1]

    # Calculate annualized return
    days = len(realPrices) - timesteps
    years = days / 365
    annualizedReturn = (1 + profit) ** (1 / years) - 1

    print("Days Elapsed: ", days)
    print("Years Elapsed: ", years)
    print("Shares: ", shares)
    print("Money: ", money)
    print("Final Share Price: ", realPrices[-1])
    print("Profit:", round(profit * 100, 2), "%")
    print("Holding Profit:", round(holdProfit * 100, 2), "%")
    print("Annualized Return:", round(annualizedReturn * 100, 2), "%")

    # Remove the part before we begin trading
    # predictedPrices = predictedPrices[timesteps:]
    # realPrices = realPrices[timesteps:]

    # # graphTest(predictedPrices, realPrices, netWorth)

def testSingleStock(symbol: str, timesteps: int = 40, days: int = 365 * 10, trainingRatio: float = 0.8, offsetDays: int = 0) -> None:
    # Get historical data
    today = pandas.Timestamp.today()
    today = today - pandas.Timedelta(days=offsetDays)
    start_date = today - pandas.Timedelta(days=days)

    print("Downloading data from " + start_date.strftime("%Y-%m-%d") + " to " + today.strftime("%Y-%m-%d") + "...")
    data = pandas.DataFrame(yfinance.download(symbol, start=start_date, end=today))
    print("Done!")

    print("Data length: " + str(len(data)))

    # Check TensorFlow configuration
    # print("TensorFlow configuration:")
    # print("CPUs:", tensorflow.config.list_physical_devices('CPU'))
    # print("GPUs:", tensorflow.config.list_physical_devices('GPU'))

    # Be really careful with : placement here!
    model = train(data[:int(len(data) * trainingRatio)], timesteps)

    # Test model
    test(model, data[int(len(data) * trainingRatio):], timesteps)

def testMultiStock(symbols: list[str], timesteps: int = 40, days: int = 365 * 10, trainingRatio: float = 0.8, offsetDays: int = 0) -> None:
    today = pandas.Timestamp.today()
    today = today - pandas.Timedelta(days=offsetDays)
    start_date = today - pandas.Timedelta(days=days)

    # Get predicted and real prices for each stock
    predictedPrices = {}
    realPrices = {}
    for symbol in symbols:
        print("Getting predicted prices for " + symbol + "...")

        print("Downloading data from " + start_date.strftime("%Y-%m-%d") + " to " + today.strftime("%Y-%m-%d") + "...")
        data = pandas.DataFrame(yfinance.download(symbol, start=start_date, end=today))
        print("Done!")

        # Be really careful with : placement here!
        model = train(data[:int(len(data) * trainingRatio)], timesteps, symbol)

        # Get predictions from model
        predictedPrices[symbol] = \
            predictPrices(model, data[int(len(data) * trainingRatio) - timesteps:], timesteps)

        realPrices[symbol] = data["Close"].values[int(len(data) * trainingRatio) - timesteps:]

        del data, model
        gc.collect()

    # Initialize variables for testing
    print("Preparing variables for testing...")
    money = 100.0
    shares = {}

    for symbol in symbols:
        shares[symbol] = 0

    netWorth = [money]

    # Test model
    print("Testing model...")
    buyPrices = {}
    profitBySymbol = {}
    for i in range(timesteps, len(predictedPrices[symbols[0]]) - 1):
        if len(predictedPrices[symbols[0]]) <= i + 1 or len(realPrices[symbols[0]]) <= i + 1:
            continue

        buyList = {}
        for symbol in symbols:
            if len(predictedPrices[symbol]) <= i + 1 or len(realPrices[symbol]) <= i + 1:
                continue

            diff = predictedPrices[symbol][i + 1][0] - predictedPrices[symbol][i][0]
            if diff > 0:
                # Add to list to buy
                buyList[symbol] = diff
            elif symbol in shares and shares[symbol] > 0:
                # Sell shares
                tradeProfit = shares[symbol] * (realPrices[symbol][-1] - buyPrices[symbol])
                if symbol not in profitBySymbol:
                    profitBySymbol[symbol] = 0
                profitBySymbol[symbol] += tradeProfit
                money += shares[symbol] * realPrices[symbol][i]
                shares[symbol] = 0

        # Convert buy list into % of total
        total = 0
        for symbol in buyList:
            total += buyList[symbol]

        for symbol in buyList:
            buyList[symbol] /= total

        # Buy shares
        buyingPower = money
        for symbol in buyList:
            buyPrices[symbol] = realPrices[symbol][i]
            shares[symbol] += buyList[symbol] * buyingPower / realPrices[symbol][i]
            money -= buyList[symbol] * buyingPower

        # Calculate net worth
        netWorthToday = money
        for symbol in symbols:
            netWorthToday += shares[symbol] * realPrices[symbol][i]
        
        netWorth.append(netWorthToday)

        # Print progress
        print("Day " + str(i) + ":", netWorthToday, "Money:", money)
        for symbol in symbols:
            print("\t" + symbol + ":", shares[symbol], "Shares -", realPrices[symbol][i] * shares[symbol], " USD")

    # Sell all shares
    for symbol in symbols:
        # Calculate profit from this trade
        tradeProfit = shares[symbol] * (realPrices[symbol][-1] - buyPrices[symbol])
        if symbol not in profitBySymbol:
            profitBySymbol[symbol] = 0
        profitBySymbol[symbol] += tradeProfit
        print("Selling", shares[symbol], "shares of", symbol, "for", realPrices[symbol][-1] * shares[symbol], \
            "USD - Profit:", tradeProfit, "USD")
        money += shares[symbol] * realPrices[symbol][-1]
        shares[symbol] = 0

    # Calculate % profit and annualized return
    profit = money - 100
    profitPercent = profit / 100

    days = len(predictedPrices[symbols[0]])
    years = days / 365
    annualizedReturn = (1 + profitPercent) ** (1 / years) - 1

    print("Days Elapsed: ", days)
    print("Years Elapsed: ", years)
    print("Shares: ", shares)
    print("Money: ", money)
    print("Profit:", round(profit, 2))
    print("Profit %:", round(profitPercent * 100, 2))
    print("Annualized Return %:", round(annualizedReturn * 100, 2))

    # Log profit by symbol
    print("Profit by Symbol:")
    for symbol in symbols:
        print(symbol + " Profit:", profitBySymbol[symbol] if symbol in profitBySymbol else "0", \
            "(% of total profit: " + str(round(profitBySymbol[symbol] / profit * 100, 2)) + "%)")

    graphMultiStockTest(netWorth)
