from sheets import log
from trading import startLoop
from testing import testMultiStock
from api import startStreamProcess
from stocklist import stocklist

# testMultiStock(stocklist, days=365*20, trainingRatio=0.4)
# exit()

# Only run if this is the main process
if(__name__ == "__main__"):
    log("Starting main process...")
    startStreamProcess()
    startLoop()
    exit()
