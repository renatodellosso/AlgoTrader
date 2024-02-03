from datetime import datetime
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
from sheets import getTransactionJournalRow, insertRowAtTop, log, logTransaction, read, sort, write

# Init client
print("Initializing Alpaca client...")
tradingClient = TradingClient(alpacaId, alpacaSecret, paper=True)

# Set up stream
async def updateHandler(data: RawData) -> None:
    try:
        eventType = data.event
        order: Order = data.order
        id = order.id
        symbol = order.symbol
        side = order.side
        shares = order.qty if order.filled_qty == 0 else order.filled_qty

        logTransaction(symbol, id, str(eventType) + "-" + ("BUY" if side == OrderSide.BUY else "SELL"), \
            float(shares) if shares is not None else "N/A", \
            float(order.filled_avg_price) if order.filled_avg_price is not None else "N/A")
        
        if eventType == "fill":
            if side == OrderSide.BUY:
                rowIndex = getTransactionJournalRow(symbol)

                if rowIndex is not None:
                    log("Updating transaction journal...")
                    
                    # Update journal
                    entry = read("Journal!A" + str(rowIndex) + ":D" + str(rowIndex))[0]

                    # Update buy price
                    avgPrice = (float(entry[1]) * float(entry[3]) + order.filled_avg_price * shares) \
                        / (float(entry[3]) + shares)
                    entry[1] = avgPrice
                    entry[3] = float(entry[3]) + shares

                    write("Journal!A" + str(rowIndex) + ":D" + str(rowIndex), [entry])

                    log("Transaction journal updated!")
                else:
                    log("Adding new entry to journal!")

                    # Add new entry
                    insertRowAtTop("743025071")
                    write("Journal!A2:K2", \
                        [[symbol, order.filled_avg_price, datetime.now(), shares, "", "", "10/14/2173 0:00:00", \
                        "=EQ(D2,G2)", '=IF(H2,F2-C2,"")', '=IF(H2,E2-B2,"")', '=J2>0']])
            elif side == OrderSide.SELL:
                rowIndex = getTransactionJournalRow(symbol)

                if rowIndex is not None:
                    log("Updating transaction journal...")

                    # Update journal
                    entry = read("Journal!A" + str(rowIndex) + ":G" + str(rowIndex))[0]

                    sharesSold = entry[6]
                    if sharesSold == "":
                        sharesSold = 0

                    # Update sell price
                    if entry[4] == "":
                        entry[4] = order.filled_avg_price
                    else:
                        prevPrice = float(entry[4])
                        entry[4] = (prevPrice * sharesSold + order.filled_avg_price * shares) \
                            / (sharesSold + shares)           

                    # Update shares sold
                    entry[6] = float(sharesSold) + shares

                    # Update sell date
                    entry[5] = datetime.now()

                    write("Journal!A" + str(rowIndex) + ":H" + str(rowIndex), [entry])

                    log("Transaction journal updated!")

            # Sort sheet so unfilled transactions stay at top
            sort("743025071", 5)
    except Exception as e:
        print("Error handling stream update: " + str(e))

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

def getEquity() -> float:
    return float(tradingClient.get_account().equity)

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
        log("Invalid number of shares!")
        return False

    # Check if we can trade this security
    security = getSecurity(symbol)
    if(not security.tradable):
        log("Security " + symbol + " is not tradable!")
        return False
    
    # Fetch the price from yfinance
    price = float(yfinance.Ticker(symbol).info['ask'])

    orderCost = price * shares
    print("Order cost: $" + str(round(orderCost, 2)) + " ($" + str(round(price, 2)) + " * " + str(shares) + ")")

    if orderCost < 1:
        log("Order cost is less than $1! Skipping...")
        return False

    # Check if we have enough money
    balance = getBuyingPower()
    print("Balance: $" + str(balance))
    if(balance < orderCost):
        shares = balance / price
        orderCost = price * shares
        log("Insufficient funds! Buying " + str(shares) + " shares instead...")
    
    if orderCost < 1:
        log("Order cost is less than $1! Skipping...")
        return False

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
    log("Placing order for " + str(object=shares) + " shares of " + symbol + " for a total value of $" + str(round(price * shares, 2)) + "...")

    # Generate order data
    # GTC is Good Til Cancelled
    # We use DAY so we can have fractional orders
    orderData = MarketOrderRequest(symbol=symbol, qty=shares, side=OrderSide.SELL, time_in_force=TimeInForce.DAY)

    # Submit order
    order = tradingClient.submit_order(orderData)

    log("Order placed!")
    return True