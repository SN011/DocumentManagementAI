
import os
import json
import subprocess
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load credentials from service account key file
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'C:\\DEV\\WebdevFolder\\realestateai-doc-mgr-3a0e2f411c8d.json'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, SCOPES)

# Create the Drive API client
service = build('drive', 'v3', credentials=credentials)

def move_file_to_folder(file_id, folder_id):
    try:
        # Retrieve the existing parents to remove
        file = service.files().get(fileId=file_id, fields='parents').execute()
        previous_parents = ",".join(file.get('parents'))
        
        # Move the file to the new folder
        file = service.files().update(
            fileId=file_id,
            addParents=folder_id,
            removeParents=previous_parents,
            fields='id, parents'
        ).execute()
        print(f'Moved file {file_id} to folder {folder_id}')
    except HttpError as error:
        print(f'An error occurred: {error}')

def create_folder(folder_name):
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    try:
        file = service.files().create(body=file_metadata, fields='id').execute()
        print(f'Folder "{folder_name}" created with ID: {file.get("id")}')
        return file.get('id')
    except HttpError as error:
        print(f'An error occurred: {error}')

def share_folder_with_user(folder_id, user_email):
    try:
        permission = {
            'type': 'user',
            'role': 'reader',
            'emailAddress': user_email
        }
        service.permissions().create(fileId=folder_id, body=permission).execute()
        print(f'Folder {folder_id} shared with {user_email}')
    except HttpError as error:
        print(f'An error occurred: {error}')

# Example usage:
# Create a new folder
folder_id = create_folder('My New Folder')

# Move a file to the new folder
file_id = '1bvvzgPtAwo8hFCU1o3TqzdWY9qdxAVC5'  # Replace with the ID of the file you want to move
folder_id = '1_V6bAUWkvkWNBAhJt6_oc7LaBsv9r5HMO361WJksqpU'  # Replace with the ID of the folder you want to move the file to
move_file_to_folder(file_id, folder_id)

# Share the folder with a user
user_email = 'user@example.com'  # Replace with the email address of the user you want to share with
share_folder_with_user(folder_id, user_email)
