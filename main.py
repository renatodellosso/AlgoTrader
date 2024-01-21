from sheets import log
from trading import startLoop
from testing import testSingleStock

# testSingleStock("BAC")
# exit()

# Only run if this is the main process
if(__name__ == "__main__"):
    log("Starting main process...")
    startLoop()
    exit()
