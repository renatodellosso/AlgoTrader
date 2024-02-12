from multiprocessing.managers import DictProxy
import sys
from time import sleep
from alpaca.common import RawData
from multiprocessing import Manager

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
    
    if triangle > 1:
        return (firstSymbol, secondSymbol), triangle
    return (secondSymbol, firstSymbol), 1 / triangle

def tradeCallback(data: RawData, transactionOrder: DictProxy):
    symbol = data.order.symbol
    event = data.event

    baseSymbol = symbol.split("/")[0]
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

    print("Best triangle:", bestTriangle, ":", triangles[bestTriangle])

    global transactionOrder
    print("Transaction order before:", transactionOrder)
    transactionOrder.clear()
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

    while True:
        updateTransactionOrder()
        print("Transaction order:", transactionOrder)
        sleep(60)