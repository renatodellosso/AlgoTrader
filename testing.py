import numpy
import pandas
from keras import Sequential
from sklearn.preprocessing import MinMaxScaler
from graphing import graphTest

def predictToday(model: Sequential, data: pandas.DataFrame, timesteps: int = 40) -> float:
    realPrice = data.iloc[:, 1:2].values
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
    realPrice = data.iloc[:, 1:2].values
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

def test(model: Sequential, data: pandas.DataFrame, timesteps: int = 40) -> None:
    print("Preparing to test model...")
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