import numpy
from graphing import graphTest

def test(predictedPrices: numpy.ndarray, realPrices: numpy.ndarray) -> None:
    # Convert predictedPrices and realPrices to 1D arrays
    predictedPrices = predictedPrices.flatten()
    realPrices = realPrices.flatten()

    money = realPrices[0]
    print("Starting Money: " + str(money))
    shares = 0

    actionsX = []
    actionsY = []
    actionsC = []
    for i in range(1, len(predictedPrices)):
        if money > 0 and predictedPrices[i] > predictedPrices[i - 1]:
            # Buy
            shares = money / realPrices[i]
            money = 0
            actionsX.append(i)
            actionsY.append(realPrices[i])
            actionsC.append('green')
        elif shares > 0 and predictedPrices[i] < predictedPrices[i - 1]:
            # Sell
            money = shares * realPrices[i]
            shares = 0
            actionsX.append(i)
            actionsY.append(realPrices[i])
            actionsC.append('red')

    money += shares * realPrices[-1]
    shares = 0

    print("Shares: ", shares)
    print("Money: ", money)
    print("Final Share Price: ", realPrices[-1])

    graphTest(predictedPrices, realPrices, actionsX, actionsY, actionsC)