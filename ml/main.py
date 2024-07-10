from trading import dailyTrade
import sys
sys.path.append('../AlgoTrader')
from sheets import log
from api import startStreamProcess
from stocklist import stocklist

# Only run if this is the main process
if(__name__ == "__main__"):
    log("Starting main process...")
    startStreamProcess()
    dailyTrade()
    exit()
