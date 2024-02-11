from datetime import datetime
import os.path
from uuid import UUID

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build
import psutil
import platform

from env import sheetsId
from ml.stocklist import stocklist

try:
    # If modifying these scopes, delete the file token.json.
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('sheetscreds.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('sheets', 'v4', credentials=creds)
except RefreshError:
    print("Error refreshing sheets token. Try deleting token.json and reauthorizing the application. Exiting...")
    exit()

def log(msg: str, waitForRam: bool = True) -> None:
    try:
        print("[LS]:", msg)

        insertRowAtTop("0")

        ramUsage = psutil.virtual_memory().percent

        # Write the message to the top row
        values = [
                [datetime.now().strftime("%d/%m/%Y: %H:%M:%S"), msg, platform.node(), psutil.cpu_percent()/100, \
                    ramUsage/100, round(psutil.Process().memory_info().rss/ 1024 ** 2)]
            ]
        
        write("A2:F2", values)

    except Exception as e:
        print("Error logging to sheets: " + str(e))

def insertRowAtTop(sheetId: str) -> None:
    requestBody = {
        "requests": [
            {
                "insertDimension": {
                    "range": {
                        "sheetId": sheetId,
                        "dimension": "ROWS",
                        "startIndex": 1,
                        "endIndex": 2
                    },
                    "inheritFromBefore": False
                }
            }
        ]
    }

    request = service.spreadsheets().batchUpdate(spreadsheetId=sheetsId, body=requestBody)
    request.execute()

def sort(sheetId: str, sortCol: int) -> None:
    requestBody = {
        "requests": [
            {
                "sortRange": {
                    "range": {
                        "sheetId": sheetId,
                        "startRowIndex": 1,
                        "endRowIndex": 1000,
                        "startColumnIndex": 0,
                        "endColumnIndex": 10
                    },
                    "sortSpecs": [
                        {
                            "dimensionIndex": sortCol,
                            "sortOrder": "DESCENDING"
                        }
                    ]
                }
            }
        ]
    }

    request = service.spreadsheets().batchUpdate(spreadsheetId=sheetsId, body=requestBody)
    request.execute()

def write(range: str, values: list[list[str]]) -> None:
    requestBody = {
        "range": range,
        "majorDimension": "ROWS",
        "values": values
    }

    request = service.spreadsheets().values().update(spreadsheetId=sheetsId, range=range, \
        valueInputOption="USER_ENTERED", body=requestBody)
    request.execute()

def read(range: str) -> list[list[str]]:
    res = service.spreadsheets().values().get(spreadsheetId=sheetsId, range=range).execute()
    return res.get('values', [])

def logTransaction(symbol: str, id: UUID, event: str, shares: float | str, price: float | str) -> None:
    try:
        if shares is float and price is float:
            totalPrice = round(shares * price, 2)
        else: totalPrice = "N/A"
        print("[LST]:", symbol, "ID:", id, event, "Shares:", round(shares, 2) if shares is float else shares, \
              "Price:", round(price, 2) if price is float else price, "Total Price:", totalPrice)

        # Insert a row at the top
        insertRowAtTop("328859340")

        values = [
                [datetime.now().strftime("%d/%m/%Y: %H:%M:%S"), str(id), symbol, str(event), \
                    str(round(shares, 2)) if shares is float else shares, \
                    str(round(price, 2)) if price is float else price, totalPrice]
            ]
        write("Transactions!A2:G2", values)
    except Exception as e:
        print("Error logging to sheets: " + str(e))

def isTransactionOpen() -> bool:
    try:
        res = read("Journal!D2:D2")
        if res is not None and len(res) > 0:
            return res[0][0] == "Open"
        else: return False
    except Exception as e:
        print("Error checking if transaction is open: " + str(e))
        return False
    
def getTransactionJournalRow(symbol: str) -> int | None:
    try:
        res = read("Journal!A2:H" + str(len(stocklist)))
        if res is not None and len(res) > 0:
            for i in range(len(res)):
                row = res[i]

                # Skip empty rows
                if len(row) < 7:
                    continue 

                # If the symbol matches and the sell price is empty, the transaction is open
                if row[0] == symbol and row[7] == "OPEN":
                    return i + 2 # Add 2 because we start on the 2nd row
        return None
    except Exception as e:
        print("Error checking if transaction is open: " + str(e))
        return None
