import numpy
import pandas
import yfinance
from sklearn.preprocessing import MinMaxScaler
from training import train
from graphing import graphChange
from testing import test

timesteps = 60
days = 365 * 20
symbol = "AAPL"

# Get historical data
today = pandas.Timestamp.today()
start_date = today - pandas.Timedelta(days=days)

print("Downloading data from " + start_date.strftime("%Y-%m-%d") + " to " + today.strftime("%Y-%m-%d") + "...")
data = pandas.DataFrame(yfinance.download(symbol, start=start_date, end=today))
print("Done!")

model = train(symbol, days, timesteps)

# Test model
print("Preparing to test model...")
testData = data
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
test(predictedPrice, realPrice)