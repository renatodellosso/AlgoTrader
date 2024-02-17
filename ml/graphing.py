import numpy
import matplotlib.pyplot as plt

def graphChange(predictedPrice: numpy.ndarray, realPrice = numpy.ndarray) -> None:
    # Transform predictedPrice into % change
    predictedChange = [[0]]
    for i in range(1, len(predictedPrice)):
        predictedChange.append((predictedPrice[i] - predictedPrice[i - 1]) / predictedPrice[i - 1])
    predictedChange = numpy.array(predictedChange)

    # Transform realPrice into % change
    realChange = [[0]]
    for i in range(1, len(realPrice)):
        realChange.append((realPrice[i] - realPrice[i - 1]) / realPrice[i - 1])
    realChange = numpy.array(realChange)

    # Plot results
    print("Plotting results...")
    plt.plot(realChange, color='black', label='Real Price')
    plt.plot(predictedChange, color='green', label='Predicted Price')
    plt.title('Stock Price Prediction')
    plt.xlabel('Time')
    plt.ylabel('Stock Price')
    plt.legend()
    plt.show()

def graphTest(predictedPrice: numpy.ndarray, realPrice: numpy.ndarray, netWorth: list, \
        actionsX: list = [], actionsY: list = [], actionsC: list = []) -> None:
    # Convert predictedPrices and realPrices to 1D arrays
    predictedPrice = predictedPrice.flatten()
    realPrice = realPrice.flatten()

    # Calculate difference between netWorth and realPrice
    netWorthDiff = numpy.array(netWorth)
    netWorthDiff = netWorthDiff.flatten()
    netWorthDiff -= realPrice

    # Create reference lines
    startPrice = [realPrice[0]] * len(realPrice)
    zero = [0] * len(realPrice)

    # Plot results
    print("Plotting results...")
    plt.plot(realPrice, color='black', label='Real Price')
    plt.plot(predictedPrice, color='yellow', label='Predicted Price')
    plt.plot(netWorth, color='blue', label='Net Worth')
    plt.plot(netWorthDiff, color='red', label='Net Worth Diff')
    plt.plot(zero, color='black', label='Zero')
    plt.plot(startPrice, color='black', label='Initial Price')
    plt.scatter(actionsX, actionsY, color=actionsC, label='Actions')
    plt.title('Algo Trade Test Results')
    plt.xlabel('Time')
    plt.ylabel('Stock Price')
    plt.legend()
    plt.show()

# Outdated, use the one in testing.py instead
def graphMultiStockTest(networth: list) -> None:
    # Plot results
    print("Plotting results...")
    plt.plot(networth, color='blue', label='Net Worth')
    plt.plot([100] * len(networth), color='black', label='Starting Net Worth')
    plt.title('Algo Trade Test Results')
    plt.xlabel('Time')
    plt.ylabel('Net Worth')
    plt.legend()
    plt.show()