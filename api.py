from datetime import datetime
import math
from multiprocessing import Process
from multiprocessing.managers import DictProxy
from time import sleep
from typing import Callable
from alpaca.trading.client import TradingClient
from alpaca.trading.stream import TradingStream
from alpaca.common import RawData
from alpaca.broker.client import Asset, Order
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import requests
import yfinance
from env import alpacaId, alpacaSecret
from sheets import getTransactionJournalRow, insertRowAtTop, log, logTransaction, read, sort, write

# Init client
print("Initializing Alpaca client...")
tradingClient = TradingClient(alpacaId, alpacaSecret, paper=True)

tradeCallbacks: list[Callable[[RawData, DictProxy], None]] = []

# Set up stream
async def updateHandler(data: RawData) -> None:
    print("Stream update received!")

    # Trade callbacks is sometimes a single function, so we need to convert it to a list
    # Don't know how it ends up as a single function, but it does
    global tradeCallbacks, sharedData
    if tradeCallbacks is not list:
        tradeCallbacks = [tradeCallbacks]

    # Run callbacks
    print("Running trade callbacks...")
    try:
        for callback in tradeCallbacks:
            # I have no clue why this is necessary, but it is
            while type(callback) is list:
                callback = callback[0]
            callback(data, sharedData)
    except Exception as e:
        print("Error running trade callbacks: " + str(e))

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
        
        return

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

def initStream(callbacks: list[Callable[[RawData, DictProxy], None]], sharedDict: DictProxy | None) -> None:
    print("Initializing Alpaca stream...")

    global tradeCallbacks
    tradeCallbacks = callbacks
    print("Trade callbacks set!")

    global sharedData
    sharedData = sharedDict

    tradingStream = TradingStream(alpacaId, alpacaSecret, paper=True)
    tradingStream.subscribe_trade_updates(updateHandler)

    print("Alpaca stream running...")
    tradingStream.run()

    print("Alpaca stream stopping...")
    tradingStream.stop()

def startStreamProcess(sharedDict: DictProxy = None) -> None:
    process = Process(target=initStream, args=(tradeCallbacks, sharedDict))
    process.start()
    print("Alpaca stream process started! Exit code:", process.exitcode)

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

def getCryptoPair(paySymbol: str, receiveSymbol: str, tryFlip: bool = True) -> float | None:
    symbol = paySymbol + "/" + receiveSymbol

    url = "https://data.alpaca.markets/v1beta3/crypto/us/latest/quotes?symbols=" + symbol
    headers = {"accept": "application/json"}

    try:
        response = requests.get(url, headers=headers)
    except requests.exceptions.RequestException as e:
        print("Error fetching crypto pair", symbol, ":", e)
        return None
    
    json = response.json()

    try:
        return json["quotes"][symbol]["ap"]
    except KeyError:
        # We may want to remove this. It's unclear if we can go backwards
        if tryFlip:
            return 1 / getCryptoPair(receiveSymbol, paySymbol, False)
        return None
    
def buyCrypto(buySymbol: str, paySymbol: str, payAmt: float | None = None) -> None:
    if payAmt is None:
        if paySymbol == "USD":
            payAmt = getBuyingPower()
        else:
            payAmt = getPosition(paySymbol + "USD")
    else:
        if paySymbol == "USD":
            payPosition = getBuyingPower()
        else:
            payPosition = getPosition(paySymbol + "USD")

    print("Buying", buySymbol, "with", payAmt, paySymbol)

    # Check if we have enough of the pay symbol
    if 'payPosition' in locals():
        payAmt = min(payAmt, payPosition)

    # Find the right symbol to buy
    symbol = buySymbol + "/" + paySymbol
    side = OrderSide.BUY
    try:
        tradingClient.get_asset(symbol)
    except:
        symbol = paySymbol + "/" + buySymbol
        side = OrderSide.SELL

    # print("Using symbol", symbol)

    # Convert payAmt to amt of buySymbol
    pair = 1 / getCryptoPair(paySymbol, buySymbol) \
        if side == OrderSide.BUY \
        else getCryptoPair(buySymbol, paySymbol)
    # print("Pair:", pair, buySymbol, "per", paySymbol)
    # print("Pay amount:", payAmt, paySymbol)
    if "USD" in symbol:
        payAmt = math.floor(payAmt) * 0.95
        # print("Pay amount (floored, 95%):", payAmt, paySymbol)
    buyAmt = payAmt / pair
    # print("Buy amount:", buyAmt, buySymbol)

    # Generate order data
    orderData = MarketOrderRequest(symbol=symbol, qty=buyAmt if side == OrderSide.BUY else payAmt, \
        side=side, time_in_force=TimeInForce.GTC)
    # print("Order data:", orderData)
    tradingClient.submit_order(orderData)
    print("Order placed!")
