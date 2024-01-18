import numpy
import pandas
import yfinance
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, LSTM, Dropout

from sheets import log

def train(symbol: str, days: int, interval: str = "1d", timesteps: int = 60) -> Sequential:
    # Get historical data
    today = pandas.Timestamp.today()
    start_date = today - pandas.Timedelta(days=days)

    print("Downloading data from " + start_date.strftime("%Y-%m-%d") + " to " + today.strftime("%Y-%m-%d") + "...")
    data = pandas.DataFrame(yfinance.download(symbol, start=start_date, end=today, interval=interval))
    print("Done!")

    return train(data, timesteps)

def train(data: pandas.DataFrame, timesteps: int = 40) -> Sequential | None:
    try:
        # Configure model
        log("Configuring model...")

        trainingRatio = 0.8 # What % of data to use for training

        trainData = data[:int(len(data) * trainingRatio)]

        # Scale data
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(trainData)

        # Add timesteps
        log("Adding timesteps...")
        xTrain = []
        yTrain = []
        for i in range(timesteps, len(scaled_data)):
            xTrain.append(scaled_data[i - timesteps:i, 0])
            yTrain.append(scaled_data[i, 0])
        xTrain, yTrain = numpy.array(xTrain), numpy.array(yTrain)
        xTrain = numpy.reshape(xTrain, (xTrain.shape[0], xTrain.shape[1], 1))

        # Configure layers
        log("Configuring layers...")
        model = Sequential()
        model.add(LSTM(units=50, return_sequences=True, input_shape=(xTrain.shape[1], 1)))
        model.add(Dropout(0.2))
        model.add(LSTM(units=50, return_sequences=True))
        model.add(Dropout(0.2))
        model.add(LSTM(units=50))
        model.add(Dropout(0.2))
        model.add(Dense(units=1))

        # Compile model
        log("Compiling model...")
        model.compile(optimizer='adam', loss='mean_squared_error')

        # Record starting time
        startTime = pandas.Timestamp.today()

        # Train model
        log("Training model...")
        model.fit(xTrain, yTrain, epochs=100, batch_size=64)

        # Log training time
        endTime = pandas.Timestamp.today()
        timeTaken = endTime - startTime
        log("Done! Training time: " +  str(timeTaken))

        return model
    except Exception as e:
        log("Error Training Model: " + str(e))
        return None