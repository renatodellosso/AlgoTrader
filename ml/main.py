from sheets import log
from trading import startLoop
from api import startStreamProcess
from stocklist import stocklist

# Only run if this is the main process
if(__name__ == "__main__"):
    log("Starting main process...")
    startStreamProcess()
    startLoop()
    exit()
