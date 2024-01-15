import numpy
import pandas
import matplotlib.pyplot as plt
import yfinance
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, LSTM, Dropout

# Get historical data
today = pandas.Timestamp.today()
start_date = today - pandas.Timedelta(days=365 * 5)

print("Downloading data from " + start_date.strftime("%Y-%m-%d") + " to " + today.strftime("%Y-%m-%d") + "...")
data = pandas.DataFrame(yfinance.download('AAPL', start=start_date, end=today))
print("Done!")

trainingRatio = 0.8 # What % of data to use for training

trainData = data[:int(len(data) * trainingRatio)]

# Scale data
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(trainData)

# Add timesteps
xTrain = []
yTrain = []
timesteps = 60
for i in range(timesteps, len(scaled_data)):
    xTrain.append(scaled_data[i - timesteps:i, 0])
    yTrain.append(scaled_data[i, 0])
xTrain, yTrain = numpy.array(xTrain), numpy.array(yTrain)
xTrain = numpy.reshape(xTrain, (xTrain.shape[0], xTrain.shape[1], 1))

# Configure model
model = Sequential()
model.add(LSTM(units=50, return_sequences=True, input_shape=(xTrain.shape[1], 1)))
model.add(Dropout(0.2))
model.add(LSTM(units=50, return_sequences=True))
model.add(Dropout(0.2))
model.add(LSTM(units=50))
model.add(Dropout(0.2))
model.add(Dense(units=1))
model.compile(optimizer='adam', loss='mean_squared_error')

# Train model
print("Training model...")
model.fit(xTrain, yTrain, epochs=100, batch_size=64)
print("Done!")

# Test model
print("Preparing to test model...")
testData = data
realPrice = data.iloc[:, 1:2].values
datasetTotal = data["Open"]
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

# Plot results
print("Plotting results...")
plt.plot(realPrice, color='black', label='Real Price')
plt.plot(predictedPrice, color='green', label='Predicted Price')
plt.title('Stock Price Prediction')
plt.xlabel('Time')
plt.ylabel('Stock Price')
plt.legend()
plt.show()