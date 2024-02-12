import sys
sys.path.append('../AlgoTrader')
from api import getCryptoPair

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

pairs = {
    "BTC": ("BCH", "ETH", "LTC", "UNI"),
    "USDT": ("AAVE", "BCH", "BTC", "ETH", "LINK", "LTC", "UNI"),
    "USDC": ("AAVE", "AVAX", "BAT", "BCH", "BTC", "CRV", "DOT", "ETH", "GRT", "LINK", "LTC", "MKR", "SHIB", "UNI", "XTZ")
}

for firstSymbol, partners in pairs.items():
    for secondSymbol in partners:
        triangle = getOptimalTriangle(firstSymbol, secondSymbol)
        if(triangle is not None):
            print(triangle)
        else:
            print("No triangle found for", firstSymbol, secondSymbol)