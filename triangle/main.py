from multiprocessing.managers import DictProxy
from time import sleep
from alpaca.common import RawData
from alpaca.trading.enums import OrderSide
from multiprocessing import Manager

import sys
sys.path.append('../AlgoTrader')
from api import buyCrypto, getCryptoPair, startStreamProcess, tradeCallbacks

def getTriangle(firstSymbol: str, secondSymbol: str) -> float | None:
    # Get the entry pair
    entryPair = getCryptoPair(firstSymbol, "USD")
    if(entryPair is None):
        print("Entry pair is None")
        return None
    # print("Entry: USD to", firstSymbol, ":", entryPair) 
    
    # Get the middle pair
    middlePair = getCryptoPair(firstSymbol, secondSymbol)
    if(middlePair is None):
        print("Middle pair is None")
        return None
    # print("Middle:", firstSymbol, "to", secondSymbol, ":", middlePair)
    
    # Get the exit pair
    exitPair = getCryptoPair(secondSymbol, "USD")
    if(exitPair is None):
        print("Exit pair is None")
        return None
    # print("Exit:", secondSymbol, "to USD :", exitPair)
    
    # Calculate the triangle
    return 1 / entryPair * middlePair * exitPair

# Returns (pair, triangle) or None
def getOptimalTriangle(firstSymbol: str, secondSymbol: str) -> tuple[tuple[str, str], float] | None:
    triangle = getTriangle(firstSymbol, secondSymbol)

    if(triangle is None):
        return None
    
    # print("Triangle:", firstSymbol, secondSymbol, ":", triangle)
    if triangle > 1:
        return (firstSymbol, secondSymbol), triangle
    return getOptimalTriangle(secondSymbol, firstSymbol)

def tradeCallback(data: RawData, transactionOrder: DictProxy):
    symbol = data.order.symbol
    event = data.event

    print(data.order.side)
    baseSymbol = symbol.split("/")[int(data.order.side != OrderSide.BUY)]
    print("Trade callback! Symbol:", symbol, "Event:", event, "Base Symbol:", baseSymbol)

    if event == "fill":
        print("Transaction Order:", transactionOrder)
        if baseSymbol in transactionOrder:
            nextSymbol = transactionOrder[baseSymbol]
            print("Next symbol:", nextSymbol)

            buyCrypto(nextSymbol, baseSymbol)
        else:
            print("No more transactions to make")

def updateTransactionOrder():
    print("Updating transaction order...")

    global transactionOrder
    triangles = {}

    for firstSymbol, partners in pairs.items():
        for secondSymbol in partners:
            triangle = getOptimalTriangle(firstSymbol, secondSymbol)
            if(triangle is not None):
                # print(triangle)
                triangles[triangle[0]] = triangle[1]
            # else:
                # print("No triangle found for", firstSymbol, secondSymbol)

    # Find the best triangle
    bestTriangle = max(triangles, key=triangles.get)

    # Remove all triangles with profits less than 0.25% (this is the fee for the trade)
    # See herer: https://docs.alpaca.markets/docs/crypto-fees
    triangles = {k: v for k, v in triangles.items() if v > 1.0025}

    global transactionOrder
    if len(triangles) == 0:
        print("No profitable triangles found")
        print("Best triangle:", bestTriangle)

        # Set everything in transaction to point to USD and delete USD
        for key in transactionOrder.keys():
            transactionOrder[key] = "USD"
        if "USD" in transactionOrder:
            del transactionOrder["USD"]
        
        return

    print("Triangles:", triangles)
    print("Best triangle:", bestTriangle, ":", triangles[bestTriangle])

    # print("Best triangle:", bestTriangle, ":", triangles[bestTriangle])

    # print("Transaction order before:", transactionOrder)
    transactionOrder["USD"] = bestTriangle[0]
    transactionOrder[bestTriangle[0]] = bestTriangle[1]
    transactionOrder[bestTriangle[1]] = "USD"

if __name__ == "__main__":
    # Init manager
    manager = Manager()
    transactionOrder = manager.dict()

    tradeCallbacks.append(tradeCallback)
    startStreamProcess(transactionOrder)

    pairs = {
        "BTC": ("BCH", "ETH", "LTC", "UNI"),
        "USDT": ("AAVE", "BCH", "BTC", "ETH", "LINK", "LTC", "UNI"),
        "USDC": ("AAVE", "AVAX", "BAT", "BCH", "BTC", "CRV", "DOT", "ETH", "GRT", "LINK", "LTC", "MKR", "SHIB", "UNI", "XTZ")
    }

    isFirstTime = True
    while True:
        updateTransactionOrder()
        print("Transaction order:", transactionOrder)

        if isFirstTime:
            buyCrypto(transactionOrder["USD"], "USD")

        isFirstTime = False
        sleep(60)