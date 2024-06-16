from tools.imports import *

SCOPES = ['https://www.googleapis.com/auth/drive']

class CreateFolderTool(BaseTool):
    name = "CreateFolderTool"
    description = "Creates a new folder in Google Drive using OAuth 2.0 for secure user authentication."
    credentials_path: str = Field(..., description="Path to the credentials JSON file")

    class Config:
        extra = Extra.allow

    def __init__(self, credentials_path: str):
        super().__init__()
        self.credentials_path = credentials_path
        self.creds = None
        self.authenticate()

    def authenticate(self):
        """Authenticate the user with Google Drive API."""
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                self.creds = flow.run_local_server(port=0)
        
        self.service = build('drive', 'v3', credentials=self.creds)

    def search_folder(self, folder_name: str):
        """Search for a folder by name in Google Drive."""
        try:
            query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            results = self.service.files().list(q=query, fields="files(id, name)").execute()
            items = results.get('files', [])
            if items:
                print(f'Found folder: {items[0]["name"]} (ID: {items[0]["id"]})')
                
                return items[0]['id']
            return None
        except HttpError as error:
            print(f'An error occurred during folder search: {error}')
            return None

    def create_folder(self, folder_name: str):
        """Create a folder in Google Drive."""
        folder_id = self.search_folder(folder_name)
        if folder_id:
            print(f'Folder "{folder_name}" already exists with ID: {folder_id}')
            with open('folder_ids.txt','w') as f:
                f.write(folder_id)
            return folder_id
        
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        try:
            file = self.service.files().create(body=file_metadata, fields='id').execute()
            print(f'Folder "{folder_name}" created with ID: {file.get("id")}')
            with open('folder_ids.txt','w') as f:
                f.write(file.get('id'))
            return file.get('id')
        except HttpError as error:
            print(f'An error occurred while creating folder: {error}')
            return None

    def _run(self, folder_name: str):
        """Run the tool to create a folder in Google Drive."""
        result = self.create_folder(folder_name)
        return result if result else "Failed to create folder."

    def _arun(self):
        raise NotImplementedError("This tool does not support asynchronous operation yet.")


class MoveFileTool(BaseTool):
    name = "MoveFileTool"
    description = "Moves a file within Google Drive using OAuth 2.0 for secure user authentication. It searches for a file by name and moves it to the specified folder."
    credentials_path: str = Field(..., description="Path to the credentials JSON file")

    class Config:
        extra = Extra.allow

    def __init__(self, credentials_path: str):
        super().__init__()
        self.credentials_path = credentials_path
        self.creds = None
        self.tmp_folder_id = None
        self.authenticate()
        #self.ensure_tmp_folder()

    def authenticate(self):
        """Authenticate the user with Google Drive API."""
        print("Authenticating with Google Drive API...")
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                print("Refreshing expired credentials...")
                self.creds.refresh(Request())
            else:
                print("Running local server for authentication...")
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                self.creds = flow.run_local_server(port=0)
        
        self.service = build('drive', 'v3', credentials=self.creds)
        print("Authentication successful.")

    def ensure_tmp_folder(self):
        """Ensure the temporary folder exists."""
        create_folder_tool = CreateFolderTool(credentials_path=self.credentials_path)
        self.tmp_folder_id = create_folder_tool.create_folder('tmp')

    def search_file(self, file_name: str):
        """Search for a file by name in Google Drive."""
        print(f"Searching for file: {file_name}")
        try:
            query = f"name contains '{file_name}' and trashed=false"
            print(f"Query: {query}")
            results = self.service.files().list(q=query, fields="files(id, name)").execute()
            items = results.get('files', [])
            if not items:
                print(f'No files found with the name: {file_name}')
                return None
            for item in items:
                print(f'Found file: {item["name"]} (ID: {item["id"]})')
            return items[0]['id']  # Return the first matching file ID
        except HttpError as error:
            print(f'An error occurred during file search: {error}')
            return None
  
    def move_file(self, file_id: str, folder_id: str):
        """Move the file to the new folder."""
        print(f"Moving file ID: {file_id} to folder ID: {folder_id}")
        try:
            # Retrieve the existing parents to remove
            print("Retrieving existing parents...")
            file = self.service.files().get(fileId=file_id, fields='parents').execute()
            previous_parents = file.get('parents', [])
            if not isinstance(previous_parents, list):
                print(f"Unexpected format for parents field: {previous_parents}")
                previous_parents = []
            previous_parents_str = ",".join(previous_parents)
            print(f"Previous parents: {previous_parents_str}")

            # if not previous_parents_str:
            #     # Add the file to a temporary parent folder first
            #     print(f"No previous parents. Adding file to temporary folder first...")
            #     self.service.files().update(
            #         fileId=file_id,
            #         addParents=self.tmp_folder_id,
            #         fields='id, parents'
            #     ).execute()
            #     previous_parents_str = self.tmp_folder_id

            # Move the file to the new folder
            print("Updating file to new folder...")
            file = self.service.files().update(
                fileId=file_id,
                addParents=folder_id,
                removeParents=previous_parents_str,
                fields='id, parents'
            ).execute()
            print(f'Moved file {file_id} to folder {folder_id}')
            return f'Moved file {file_id} to folder {folder_id}. PLEEEASEEEE STOOOPPPPPP!!!!!! NO MORE!!!!!!! YOU ARE DONE!!!!'
        except HttpError as error:
            print(f'An error occurred during file move: {error}')
            return None
        except Exception as e:
            print(f'An unexpected error occurred: {e}')
            return None

    def search_folder(self, folder_name: str):
        """Search for a folder by name in Google Drive using a contains query."""
        try:
            query = f"name contains '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            results = self.service.files().list(q=query, fields="files(id, name)").execute()
            items = results.get('files', [])
            if items:
                for item in items:
                    print(f'Found folder: {item["name"]} (ID: {item["id"]})')
                return items[0]['id']
            return None
        except HttpError as error:
            print(f'An error occurred during folder search: {error}')
            return None

    def _run(self, file_name: str, folder_name: str):
        """Run the tool to search for the file and move it to the specified folder."""
        folder_id = "root" if folder_name.lower() in ["root", "general google drive"] else self.search_folder(folder_name)
        if folder_id is None:
            return "Folder not found."
        
        print(f"Running MoveFileTool with file_name: {file_name} and folder_id: {folder_id}")
        file_id = self.search_file(file_name)
        if file_id is None:
            return "File not found."
        
        result = self.move_file(file_id, folder_id)
        return result if result else "Failed to move file."

    def _arun(self):
        raise NotImplementedError("This tool does not support asynchronous operation yet.")


SCOPES = ['https://www.googleapis.com/auth/drive']

class FolderMovementTool(BaseTool):
    name = "Folder movement tool"
    description = "Manages folders in Google Drive using OAuth 2.0 for secure user authentication. Provides functionality to move folders and their contents."
    credentials_path: str = Field(..., description="Path to the credentials JSON file")

    class Config:
        extra = Extra.allow

    def __init__(self, credentials_path: str):
        super().__init__()
        self.credentials_path = credentials_path
        self.creds = None
        self.authenticate()

    def authenticate(self):
        """Authenticate the user with Google Drive API using OAuth 2.0."""
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                self.creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())
        self.service = build('drive', 'v3', credentials=self.creds)

    def search_folder(self, folder_name: str):
        """Search for a folder by name in Google Drive using a contains query."""
        try:
            query = f"name contains '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            results = self.service.files().list(q=query, fields="files(id, name)").execute()
            items = results.get('files', [])
            if items:
                for item in items:
                    print(f'Found folder: {item["name"]} (ID: {item["id"]})')
                return items[0]['id']
            return None
        except HttpError as error:
            print(f'An error occurred during folder search: {error}')
            return None
        
    def move_file_to_folder(self, file_id, folder_id):
        try:
            # Retrieve the existing parents to remove
            file = self.service.files().get(fileId=file_id, fields='parents').execute()
            previous_parents = ",".join(file.get('parents'))

            # Move the file to the new folder
            self.service.files().update(
                fileId=file_id,
                addParents=folder_id,
                removeParents=previous_parents,
                fields='id, parents'
            ).execute()
            print(f'Moved file {file_id} to folder {folder_id}')
        except HttpError as error:
            print(f'An error occurred: {error}')

    def move_folder_and_contents(self, folder_id, new_parent_folder_id):
        service = build('drive', 'v3', credentials=self.creds)
        try:
            # Move the folder itself
            self.move_file_to_folder(folder_id, new_parent_folder_id)

            # List all files and subfolders in the folder
            query = f"'{folder_id}' in parents"
            results = service.files().list(q=query, fields="files(id, mimeType)").execute()
            items = results.get('files', [])

            for item in items:
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    # Recursively move subfolders
                    self.move_folder_and_contents(item['id'], folder_id)
                else:
                    # Move files
                    self.move_file_to_folder(item['id'], folder_id)

            print(f'Moved folder {folder_id} and all its contents to {new_parent_folder_id}')
        except HttpError as error:
            print(f'An error occurred during file move: {error}')

    def move_folder_and_contents(self, folder_id, new_parent_folder_id):
        try:
            # Move the folder itself
            self.move_file_to_folder(folder_id, new_parent_folder_id)

            # List all files and subfolders in the folder
            query = f"'{folder_id}' in parents"
            results = self.service.files().list(q=query, fields="files(id, mimeType)").execute()
            items = results.get('files', [])

            for item in items:
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    # Recursively move subfolders
                    self.move_folder_and_contents(item['id'], folder_id)
                else:
                    # Move files
                    self.move_file_to_folder(item['id'], folder_id)

            print(f'Moved folder {folder_id} and all its contents to {new_parent_folder_id}')
        except HttpError as error:
            print(f'An error occurred: {error}')

    def _run(self, folder_name: str, new_parent_folder_name: str):
        """Run the tool to search for a folder by name and move its contents to a new parent folder."""

        if new_parent_folder_name.lower() in ["root", "general google drive"]:
            new_parent_folder_id = "root"
        else:
            new_parent_folder_id = self.search_folder(new_parent_folder_name)
            if not new_parent_folder_id:
                return f"New parent folder '{new_parent_folder_name}' not found."
        
        print(f"Running FolderManagementTool with folder_name: {folder_name} and new_parent_folder_id: {new_parent_folder_id}")
        folder_id = self.search_folder(folder_name)
        if folder_id is None:
            return "Folder not found."
        
        self.move_folder_and_contents(folder_id, new_parent_folder_id)
        return "Folder and contents moved successfully. PLEASE STOPPPPPPPPP!!!!!!!!!! RIGHT NOW!!!!!! YOU ARE DONE!!!!!!!! STOP!!!!!!!!"

    def _arun(self):
        raise NotImplementedError("This tool does not support asynchronous operation yet.")


SCOPES = ['https://www.googleapis.com/auth/drive']

class FileOrganizerTool(BaseTool):
    name = "FileOrganizerTool"
    description = "Organizes files in Google Drive by segregating them based on type and moving them to respective folders using OAuth 2.0 for secure user authentication."
    credentials_path: str = Field(..., description="Path to the credentials JSON file")

    class Config:
        extra = Extra.allow

    def __init__(self, credentials_path: str):
        super().__init__()
        self.credentials_path = credentials_path
        self.creds = None
        self.authenticate()

    def authenticate(self):
        """Authenticate the user with Google Drive API using OAuth 2.0."""
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                self.creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())
        self.service = build('drive', 'v3', credentials=self.creds)

    def list_unorganized_files(self, parent_folder_id=None):
        """List all files in the user's Drive that are not in an organized folder."""
        try:
            query = "mimeType != 'application/vnd.google-apps.folder' and trashed = false"
            if parent_folder_id:
                query += f" and '{parent_folder_id}' in parents"
            else:
                query += " and 'root' in parents"
            results = self.service.files().list(q=query, fields="files(id, name, mimeType, parents)").execute()
            items = results.get('files', [])
            return items
        except HttpError as error:
            print(f'An error occurred during file listing: {error}. PLEASE STOPPPPPPPPP!!!!!!!!!! RIGHT NOW!!!!!! YOU ARE DONE!!!!!!!! STOP!!!!!!!!')
            return []

    def create_folder_if_not_exists(self, folder_name: str, parent_folder_id=None):
        """Create a folder in Google Drive if it doesn't already exist."""
        try:
            # Adjust folder name with parent folder context for uniqueness
            query = f"name contains '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            if parent_folder_id:
                query += f" and '{parent_folder_id}' in parents"
            results = self.service.files().list(q=query, fields="files(id, name)").execute()
            items = results.get('files', [])
            if items:
                for item in items:
                    if item['name'].lower() == folder_name.lower():
                        return item['id']
                return items[0]['id']
            else:
                file_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                if parent_folder_id:
                    file_metadata['parents'] = [parent_folder_id]
                file = self.service.files().create(body=file_metadata, fields='id').execute()
                return file.get('id')
        except HttpError as error:
            print(f'An error occurred while creating folder: {error}. PLEASE STOPPPPPPPPP!!!!!!!!!! RIGHT NOW!!!!!! YOU ARE DONE!!!!!!!! STOP!!!!!!!!')
            return None

    def move_file_to_folder(self, file_id, folder_id):
        """Move a file to the specified folder."""
        try:
            # Retrieve the existing parents to remove
            file = self.service.files().get(fileId=file_id, fields='parents').execute()
            previous_parents = ",".join(file.get('parents'))

            # Move the file to the new folder
            self.service.files().update(
                fileId=file_id,
                addParents=folder_id,
                removeParents=previous_parents,
                fields='id, parents'
            ).execute()
            print(f'Moved file {file_id} to folder {folder_id}.')
        except HttpError as error:
            print(f'An error occurred during file move: {error}. PLEASE STOPPPPPPPPP!!!!!!!!!! RIGHT NOW!!!!!! YOU ARE DONE!!!!!!!! STOP!!!!!!!!')

    def organize_files(self, parent_folder_id=None):
        """Organize files by type and move them to respective folders."""
        files = self.list_unorganized_files(parent_folder_id)
        if not files:
            return "No unorganized files found."

        folder_mapping = {
            'application/vnd.google-apps.document': 'Documents',
            'application/vnd.google-apps.spreadsheet': 'Spreadsheets',
            'application/vnd.google-apps.presentation': 'Presentations',
            'application/pdf': 'PDFs',
            'image/jpeg': 'Images',
            'image/png': 'Images',
            'video/mp4': 'Videos',
            # Add other mappings as needed
        }

        for file in files:
            folder_name = folder_mapping.get(file['mimeType'], 'Others')
            # Append parent folder name to ensure unique folder names
            if parent_folder_id:
                parent_folder_metadata = self.service.files().get(fileId=parent_folder_id, fields='name').execute()
                parent_folder_name = parent_folder_metadata['name']
                folder_name = f"{folder_name}_{parent_folder_name}"
            folder_id = self.create_folder_if_not_exists(folder_name, parent_folder_id)
            if folder_id:
                self.move_file_to_folder(file['id'], folder_id)

        return "Files organized successfully. PLEASE STOPPPPPPPPP!!!!!!!!!! RIGHT NOW!!!!!! YOU ARE DONE!!!!!!!! STOP!!!!!!!!"

    def _run(self, parent_folder_name: str = None):
        """Run the tool to organize files in Google Drive."""
        
        parent_folder_id = None

        if parent_folder_name:
            parent_folder_id = self.create_folder_if_not_exists(parent_folder_name)
            if parent_folder_id is None:
                return "Parent folder not found.PLEASE STOPPPPPPPPP!!!!!!!!!! RIGHT NOW!!!!!! YOU ARE DONE!!!!!!!! STOP!!!!!!!!"
        else:
            parent_folder_id = None  # Ensure parent_folder_id is None for root directory
            
        result = self.organize_files(parent_folder_id)
        return result

    def _arun(self):
        raise NotImplementedError("This tool does not support asynchronous operation yet.")