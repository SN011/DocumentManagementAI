import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/gmail.send',
]

CREDENTIALS_PATH = os.getenv('CREDENTIALS_PATH')
TOKEN_PATH = 'paths/token.json'

def authenticate():
    creds = None
    # Debugging: Ensure paths are correct
    print(f"CREDENTIALS_PATH: {CREDENTIALS_PATH}")
    print(f"TOKEN_PATH: {TOKEN_PATH}")

    # Load existing credentials from the token file
    if os.path.exists(TOKEN_PATH):
        print("Loading credentials from token file.")
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    
    # If there are no valid credentials, initiate the OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired credentials.")
            creds.refresh(Request())
        else:
            print("Initiating OAuth flow.")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN_PATH, 'w') as token_file:
                token_file.write(creds.to_json())
    
    return creds

# Ensure no default credentials are being used
if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
    del os.environ['GOOGLE_APPLICATION_CREDENTIALS']
