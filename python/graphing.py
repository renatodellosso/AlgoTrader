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

def graphTest(predictedPrice: numpy.ndarray, realPrice: numpy.ndarray, actionsX: list, actionsY: list, actionsC: list) -> None:
    # Convert predictedPrices and realPrices to 1D arrays
    predictedPrice = predictedPrice.flatten()
    realPrice = realPrice.flatten()

    # Plot results
    print("Plotting results...")
    plt.plot(realPrice, color='black', label='Real Price')
    plt.plot(predictedPrice, color='green', label='Predicted Price')
    plt.scatter(actionsX, actionsY, color=actionsC, label='Actions')
    plt.title('Algo Trade Test Results')
    plt.xlabel('Time')
    plt.ylabel('Stock Price')
    plt.legend()
    plt.show()