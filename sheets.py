from datetime import datetime
import os.path
import time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
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

def log(msg: str) -> None:
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

    # Write the message to the top row
    requestBody = {
        "range": "A2:E2",
        "majorDimension": "ROWS",
        "values": [
            [datetime.now().strftime("%d/%m/%Y: %H:%M:%S"), msg, platform.node(), psutil.cpu_percent()/100, psutil.virtual_memory().percent/100]
        ]
    }

    request = service.spreadsheets().values().update(spreadsheetId=sheetsId, range="A2:E2", valueInputOption="USER_ENTERED", body=requestBody)
    request.execute()

    # If RAM usage is over 90%, wait for it to go down
    while(psutil.virtual_memory().percent > 0.9):
        print("RAM usage is over 90%! Waiting for it to go down...")
        time.sleep(60)
