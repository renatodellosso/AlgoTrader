import numpy
import pandas
import matplotlib.pyplot as plt
import yfinance
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, LSTM, Dropout

# Get historical data
today = pandas.Timestamp.today()
start_date = today - pandas.Timedelta(days=365)

print("Downloading data from " + start_date.strftime("%Y-%m-%d") + " to " + today.strftime("%Y-%m-%d") + "...")
data = yfinance.download('AAPL', start=start_date, end=today)
print("Done!")

# Scale data
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(data)

# Add timesteps
xTrain = []
yTrain = []
timesteps = 60
for i in range(timesteps, int(len(scaled_data) * 0.8)):
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
model.fit(xTrain, yTrain, epochs=100, batch_size=32)

# Test model
testData = data[int(len(data) * 0.8) - timesteps:]
realPrice = data.iloc[:, 1:2].values
datasetTotal = pandas.concat((data['Open'], testData['Open']), axis=0)
inputs = datasetTotal[len(datasetTotal) - len(testData) - timesteps:].values

inputs = inputs.reshape(-1, 6) # param1 is number of rows, param2 is size of each row
print(inputs)
inputs = scaler.transform(inputs)

xTest = []
for i in range(timesteps, len(inputs)):
    xTest.append(inputs[i - timesteps:i, 0])

xTest = numpy.array(xTest)
xTest = numpy.reshape(xTest, (xTest.shape[0], xTest.shape[1], 1))

predictedPrice = model.predict(xTest)
predictedPrice = scaler.inverse_transform(predictedPrice)

# Plot results
plt.plot(realPrice, color='black', label='Real Price')
plt.plot(predictedPrice, color='green', label='Predicted Price')
plt.title('Stock Price Prediction')
plt.xlabel('Time')
plt.ylabel('Stock Price')
plt.legend()
plt.show()