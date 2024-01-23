import multiprocessing
from time import sleep
from alpaca.trading.client import TradingClient
from alpaca.trading.stream import TradingStream
from alpaca.common import RawData
from alpaca.broker.client import Asset, Order
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import yfinance
from env import alpacaId, alpacaSecret
from sheets import log, logTransaction

# Init client
print("Initializing Alpaca client...")
tradingClient = TradingClient(alpacaId, alpacaSecret, paper=True)

# Set up stream
async def updateHandler(data: RawData) -> None:
    eventType = data.event
    order: Order = data.order
    id = order.id
    symbol = order.symbol
    side = order.side
    shares = order.qty if order.filled_qty == 0 else order.filled_qty

    logTransaction(symbol, id, str(eventType) + "-" + ("BUY" if side == OrderSide.BUY else "SELL"), \
        float(shares) if shares is not None else "N/A", \
        float(order.filled_avg_price) if order.filled_avg_price is not None else "N/A")

def initStream() -> None:
    print("Initializing Alpaca stream...")
    tradingStream = TradingStream(alpacaId, alpacaSecret, paper=True)
    tradingStream.subscribe_trade_updates(updateHandler)
    tradingStream.run()
    tradingStream.stop()

def startStreamProcess() -> multiprocessing.Process:
    process = multiprocessing.Process(target=initStream)
    process.start()
    print("Alpaca stream process started!")

if __name__ == "__main__":
    process = startStreamProcess()

    while True:
        try:
            sleep(1)
        except KeyboardInterrupt:
            print("Exiting...")
            process.terminate()
            exit()
        
print("Alpaca client initialized!")

def getBuyingPower() -> float:
    return float(tradingClient.get_account().buying_power)

def getPosition(symbol: str) -> float:
    allPositions = tradingClient.get_all_positions()
    for position in allPositions:
        if(position.symbol == symbol):
            return float(position.qty)
    return 0

def getSecurity(symbol: str) -> Asset | RawData:
    return tradingClient.get_asset(symbol)

def getOpenOrders() -> list[Order] | RawData:
    return tradingClient.get_orders()

def placeBuyOrder(symbol: str, shares: float) -> bool:
    log("Attempting to place buy order for " + str(shares) + " shares of " + symbol + "...")

    # Check if shares is valid
    if(shares <= 0):
        print("Invalid number of shares!")
        return False

    # Check if we can trade this security
    security = getSecurity(symbol)
    if(not security.tradable):
        log("Security " + symbol + " is not tradable!")
        return False
    
    # Fetch the price from yfinance
    price = float(yfinance.Ticker(symbol).info['ask'])

    orderCost = price * shares
    log("Order cost: $" + str(round(orderCost, 2)) + " ($" + str(round(price, 2)) + " * " + str(shares) + ")")

    # Check if we have enough money
    balance = getBuyingPower()
    log("Balance: $" + str(balance))
    if(balance < orderCost):
        shares = balance / price
        log("Insufficient funds! Buying " + str(shares) + " shares instead...")
    
    # Place order
    log("Placing order for " + str(shares) + " shares of " + symbol + " for a total cost of $" + str(orderCost) + "...")
    
    # Generate order data
    # GTC is Good Til Cancelled
    # We use DAY so we can have fractional orders
    orderData = MarketOrderRequest(symbol=symbol, qty=shares, side=OrderSide.BUY, time_in_force=TimeInForce.DAY)

    # Submit order
    order = tradingClient.submit_order(orderData)
    
    log("Order placed!")
    return True

def placeSellOrder(symbol: str, shares: float) -> bool:
    log("Attempting to place sell order for " + str(shares) + " shares of " + symbol + "...")

    if(shares <= 0):
        log("Invalid number of shares!")
        return False

    security = getSecurity(symbol)
    if(not security.tradable):
        log("Security " + symbol + " is not tradable!")
        return False
    
    # Check if we have enough shares
    position = getPosition(symbol)
    log("Position: " + str(position))
    if(position < shares):
        log("Insufficient shares!")
        return False
    
    # Fetch price
    price = int(yfinance.Ticker(symbol).info['bid'])
    
    # Place order
    log("Placing order for " + str(shares) + " shares of " + symbol + " for a total value of $" + str(round(price * shares, 2)) + "...")

    # Generate order data
    # GTC is Good Til Cancelled
    # We use DAY so we can have fractional orders
    orderData = MarketOrderRequest(symbol=symbol, qty=shares, side=OrderSide.SELL, time_in_force=TimeInForce.DAY)

    # Submit order
    order = tradingClient.submit_order(orderData)

    log("Order placed!")
    return True