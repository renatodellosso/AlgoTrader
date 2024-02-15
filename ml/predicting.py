import numpy
import pandas
from keras import Sequential
from keras.callbacks import Callback
from sklearn.preprocessing import MinMaxScaler

class PredictionCallback(Callback):
    # Should disable the default logging
    def on_predict_end(self, logs=None):
        pass

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
    predictedPrice = model.predict(xTest, callbacks=[PredictionCallback()])
    predictedPrice = scaler.inverse_transform(predictedPrice)

    return predictedPrice

# Returns (todayPrice, predictedPriceToday, predictedPriceTmr)
def getChangeTuple(model: Sequential, data: pandas.DataFrame, timesteps: int = 40) -> tuple:
    data = data[-(2 * 365):] # Only predict the last 2 years

    predictions = predictPrices(model, data, timesteps)
    predictedPriceToday = predictions[-2] # It's possible this is actually yesterday's price
    predictedPriceTmr = predictions[-1] # Might be today's price

    return (predictedPriceToday, predictedPriceTmr)

def getChange(model: Sequential, data: pandas.DataFrame, timesteps: int = 40) -> float:
    try:
        # Get predicted prices
        prediction = getChangeTuple(model, data, timesteps)

        # Convert from (today, tomorrow) to % change
        diff = (prediction[1] - prediction[0]) / prediction[0]

        return diff
    except Exception as e:
        print("Error getting predicted prices: " + str(e))
        return None