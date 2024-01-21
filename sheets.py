from datetime import datetime
import gc
import os.path
import time
from uuid import UUID

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from alpaca.trading.enums import OrderSide
import psutil
import platform

from env import sheetsId

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

def log(msg: str, waitForRam: bool = True) -> None:
    try:
        print("[LS]:", msg)

        # Insert a row at the top
        requestBody = {
            "requests": [
                {
                    "insertDimension": {
                        "range": {
                            "sheetId": 0,
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

        ramUsage = psutil.virtual_memory().percent

        # Write the message to the top row
        requestBody = {
            "range": "A2:F2",
            "majorDimension": "ROWS",
            "values": [
                [datetime.now().strftime("%d/%m/%Y: %H:%M:%S"), msg, platform.node(), psutil.cpu_percent()/100, \
                    ramUsage/100, round(psutil.Process().memory_info().rss/ 1024 ** 2)]
            ]
        }

        request = service.spreadsheets().values().update(spreadsheetId=sheetsId, range="A2:F2", valueInputOption="USER_ENTERED", body=requestBody)
        request.execute()
    except Exception as e:
        print("Error logging to sheets: " + str(e))

def logTransaction(symbol: str, id: UUID, side: str, shares: float, price: float) -> None:
    try:
        totalPrice = shares * price
        print("[LST]:", symbol, "ID:", id, side, "Shares:", round(shares, 2), "Price:", round(price, 2), "Total Price:", round(totalPrice, 2))

        # Get Sheet ID
        sheetIdRes = service.spreadsheets().get(spreadsheetId=sheetsId, ranges=["Transactions!A1:2"]).execute()

        # Insert a row at the top
        requestBody = {
            "requests": [
                {
                    "insertDimension": {
                        "range": {
                            "sheetId": str(sheetIdRes["sheets"][0]["properties"]["sheetId"]),
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

        # Write the message to the top row
        requestBody = {
            "range": "Transactions!A2:G2",
            "majorDimension": "ROWS",
            "values": [
                [datetime.now().strftime("%d/%m/%Y: %H:%M:%S"), str(id), symbol, side, round(shares, 2), \
                    round(price, 2), round(totalPrice, 2)]
            ]
        }

        request = service.spreadsheets().values().update(spreadsheetId=sheetsId, range="Transactions!A2:G2", \
            valueInputOption="USER_ENTERED", body=requestBody)
        request.execute()
    except Exception as e:
        print("Error logging to sheets: " + str(e))