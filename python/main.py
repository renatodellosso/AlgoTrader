import numpy
import pandas
import yfinance
import tensorflow
from sklearn.preprocessing import MinMaxScaler
from training import train
from graphing import graphChange
from testing import test

timesteps = 40 # 40 works well
days = 365 * 10 # 10 years works well
trainingRatio = 0.8 # What % of data to use for training, 0.8 is standard
offsetDays = 0
symbol = "WFC" # Symbols with 20% - 30% returns over 5Y seem to work best, such as KO, CVX, PM, BAC (v. well!), INTC, WFC (v. well!)

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

model = train(data[:int(len(data) * trainingRatio)], timesteps)

# Test model
print("Preparing to test model...")
testData = data[int(len(data) * trainingRatio):]
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

# graphChange(predictedPrice, realPrice)
test(predictedPrice, realPrice, timesteps)