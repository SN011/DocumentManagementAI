import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/calendar',
]

CREDENTIALS_PATH = os.getenv('CREDENTIALS_PATH')
TOKEN_PATH = 'paths/token.json'
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
def get_auth_flow():
    return Flow.from_client_secrets_file(
        CREDENTIALS_PATH, scopes=SCOPES,
        redirect_uri='http://35.185.35.162/oauth2callback')

def authenticate():
    creds = None

    # Load existing credentials from the token file
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # If there are no valid credentials, initiate the OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Failed to refresh token: {e}")
                os.remove(TOKEN_PATH)  # Delete the token file if refresh fails
                creds = None  # Set creds to None to initiate a new OAuth flow
        if not creds:
            flow = get_auth_flow()
            auth_url, _ = flow.authorization_url(prompt='consent')
            return auth_url

    return creds
