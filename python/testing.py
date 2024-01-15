import numpy
from graphing import graphTest

def test(predictedPrices: numpy.ndarray, realPrices: numpy.ndarray, timesteps: int) -> None:
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

    print("Shares: ", shares)
    print("Money: ", money)
    print("Final Share Price: ", realPrices[-1])
    print("Profit:", round(profit * 100, 2), "%")
    print("Holding Profit:", round(holdProfit * 100, 2), "%")

    # Remove the part before we begin trading
    predictedPrices = predictedPrices[timesteps:]
    realPrices = realPrices[timesteps:]

    graphTest(predictedPrices, realPrices, netWorth)