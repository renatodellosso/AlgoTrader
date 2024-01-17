# Read environment variables
envFile = open(".env", "r")

for line in envFile:
    splitLine = line.split("=")
    if splitLine[0] == "ALPACA_ID":
        alpacaId = splitLine[1].strip()
    elif splitLine[0] == "ALPACA_SECRET":
        alpacaSecret = splitLine[1].strip()
    elif splitLine[0] == "SHEETS_ID":
        sheetsId = splitLine[1].strip()

envFile.close()