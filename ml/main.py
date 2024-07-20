import time
from trading import dailyTrade
from threading import Event
import sys
sys.path.append('../AlgoTrader')
from sheets import log
from api import startStreamProcess
from discordbot import startBot
from exitflag import exitFlag


def main():
    log("Starting main process...")
    botThread = startBot(exitFlag)
    startStreamProcess()
    dailyTrade()
    print("Exiting main process in 5 seconds...")
    exitFlag.set()
    time.sleep(5)

# Only run if this is the main process
if(__name__ == "__main__"):
    main()
    exit()