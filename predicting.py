import numpy
import pandas
from keras import Sequential
from sklearn.preprocessing import MinMaxScaler


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