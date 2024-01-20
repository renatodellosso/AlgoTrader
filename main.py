import pandas
import yfinance
from sheets import log
from testing import test, testSingleStock
from trading import startLoop
from training import train

# Only run if this is the main process
if(__name__ == "__main__"):
    log("Starting main process...")
    startLoop()
    exit()
