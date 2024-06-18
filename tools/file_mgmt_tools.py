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

    def search_folder(self, folder_name: str, parent_folder_id: str = None):
        """Search for a folder by name in Google Drive."""
        try:
            query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            if parent_folder_id:
                query += f" and '{parent_folder_id}' in parents"
            results = self.service.files().list(q=query, fields="files(id, name)").execute()
            items = results.get('files', [])
            if items:
                print(f'Found folder: {items[0]["name"]} (ID: {items[0]["id"]})')
                return items[0]['id']
            return None
        except HttpError as error:
            print(f'An error occurred during folder search: {error}')
            return None

    def create_folder(self, folder_name: str, parent_folder_id: str = None):
        """Create a folder in Google Drive."""
        folder_id = self.search_folder(folder_name, parent_folder_id)
        if folder_id:
            print(f'Folder "{folder_name}" already exists with ID: {folder_id}')
            with open('folder_ids.txt', 'w') as f:
                f.write(folder_id)
            return folder_id
        
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_folder_id:
            file_metadata['parents'] = [parent_folder_id]
        try:
            file = self.service.files().create(body=file_metadata, fields='id').execute()
            print(f'Folder "{folder_name}" created with ID: {file.get("id")}')
            with open('folder_ids.txt', 'w') as f:
                f.write(file.get('id'))
            return f"HERE IS FOLDER'S ID {file.get('id')}"
        except HttpError as error:
            print(f'An error occurred while creating folder: {error}')
            return None

    def _run(self, folder_name: str, parent_folder_id: str = None, **kwargs):
        """Run the tool to create a folder in Google Drive."""
        if not parent_folder_id:
            return f"Use the ImprovedSearchTool to find the parent folder ID for '{parent_folder_id}' and pass it as an argument to this tool."

        result = self.create_folder(folder_name, parent_folder_id)
        return result if result else "Failed to create folder."

    def _arun(self):
        raise NotImplementedError("This tool does not support asynchronous operation yet.")


SCOPES = ['https://www.googleapis.com/auth/drive']

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
        self.authenticate()

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
            return f'An error occurred during file move: {error}'
        except Exception as e:
            print(f'An unexpected error occurred: {e}')
            return f'An unexpected error occurred: {e}'

    def _run(self, file_name: str = None, folder_name:str = None, folder_id: str = None, file_id: str = None, **kwargs):
        """Run the tool to search for the file and move it to the specified folder."""
        if folder_id and folder_id.lower() in ["root", "google drive", "my drive"]:
            folder_id = "root"
        elif folder_name and not folder_id:
            return f"Use the ImprovedSearchTool to find the folder ID for '{folder_name}' and pass it as an argument to this tool as parameter 'folder_id'. Be sure to pass in the folder_name as well"
        
        if file_name and folder_id and not file_id:
            return f"Use the ImprovedSearchTool to find the file ID for '{file_name}' and pass it as an argument to this tool under 'file_id' parameter. Once you have both IDs, call this tool again with the IDs to move the file. Be sure to pass in ALL OF THE FOLLOWING: folder_name, file_name, file_id, folder_id."

        if file_id and folder_id:
            result = self.move_file(file_id, folder_id)
            return result if result else "Failed to move file. Please stop all work!!!!!!!"

        return "Invalid input. Provide either file_name or file_id and folder_id."

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

            return (f'Moved folder {folder_id} and all its contents to {new_parent_folder_id}. PLEASE STOP ALL WORK!!!')
        except HttpError as error:
            print(f'An error occurred: {error}')
            return None

    # def _run(self, folder_name: str, new_parent_folder_name: str, folder_id:str = None, new_parent_folder_id:str = None):
    #     """Run the tool to search for a folder by name and move its contents to a new parent folder."""

    #     if new_parent_folder_name.lower() in ["root", "general google drive"]:
    #         new_parent_folder_id = "root"
    #     else:
    #         new_parent_folder_id = self.search_folder(new_parent_folder_name)
    #         if not new_parent_folder_id:
    #             return f"New parent folder '{new_parent_folder_name}' not found."
        
    #     print(f"Running FolderMovementTool with folder_name: {folder_name} and new_parent_folder_id: {new_parent_folder_id}")
    #     folder_id = self.search_folder(folder_name)
    #     if folder_id is None:
    #         return "Folder not found."
        
    #     self.move_folder_and_contents(folder_id, new_parent_folder_id)
    #     return "Folder and contents moved successfully. PLEASE STOPPPPPPPPP!!!!!!!!!! RIGHT NOW!!!!!! YOU ARE DONE!!!!!!!! STOP!!!!!!!!"

    # def _arun(self):
    #     raise NotImplementedError("This tool does not support asynchronous operation yet.")
    
    def _run(self, folder_name: str, new_parent_folder_name: str, folder_id:str = None, new_parent_folder_id:str = None, **kwargs):
        """Run the tool to search for a folder by name and move its contents to a new parent folder."""

        if new_parent_folder_name.lower() in ["root", "google drive", "my drive", "general google drive"]:
            new_parent_folder_id = "root"
        elif not folder_id and not new_parent_folder_id:
            return f"Use the ImprovedSearchTool to find the PARENT FOLDER ID for '{new_parent_folder_name}' and pass it as an argument to this tool. Be sure to pass in the new_parent_folder_name as an argument too"
        
        if folder_name and not folder_id:
            return f"Use the ImprovedSearchTool to find the folder ID for '{folder_name}' (which is the folder that's being moved) and pass it as an argument to this tool. Once you have both IDs, call this tool again with the IDs to move the folder. Be sure to also pass in folder_name and new_parent_folder_name PLEASE!"

        if folder_id and new_parent_folder_id:
            result = self.move_folder_and_contents(folder_id, new_parent_folder_id)
            return result if result else "Failed to move folder. PLEASE STOP ALL WORK!!!!"

        return "Invalid input. Provide either file_name or file_id and folder_id."
    
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
            unique_folder_name = folder_name
            if parent_folder_id:
                parent_folder = self.service.files().get(fileId=parent_folder_id, fields="name").execute()
                unique_folder_name += f"_{parent_folder['name']}"
            else:
                unique_folder_name += f"_MyDrive"
            query = f"name = '{unique_folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            if parent_folder_id:
                query += f" and '{parent_folder_id}' in parents"
            results = self.service.files().list(q=query, fields="files(id, name)").execute()
            items = results.get('files', [])
            print([str(item)+"\n" for item in items])
            if items:
                return items[0]['id']
            else:
                file_metadata = {
                    'name': unique_folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                if parent_folder_id:
                    file_metadata['parents'] = [parent_folder_id]
                file = self.service.files().create(body=file_metadata, fields='id').execute()
                return file.get('id')
        except HttpError as error:
            print(f'An error occurred while creating folder: {error}. PLEASE STOPPPPPPPPP!!!!!!!!!! RIGHT NOW!!!!!! YOU ARE DONE!!!!!!!! STOP!!!!!!!!')
            return None

    def get_file_permissions(self, file_id):
        """Get the permissions of a file."""
        try:
            permissions = self.service.permissions().list(fileId=file_id).execute()
            return permissions.get('permissions', [])
        except HttpError as error:
            print(f'An error occurred while getting file permissions: {error}')
            return []

    def move_file_to_folder(self, file_id, folder_id):
        """Move a file to the specified folder."""
        try:
            # Retrieve the existing parents to remove
            file = self.service.files().get(fileId=file_id, fields='parents').execute()
            previous_parents = ",".join(file.get('parents'))

            # Print permissions for debugging
            permissions = self.get_file_permissions(file_id)
            print(f"Permissions for file {file_id}: {permissions}")

            # Move the file to the new folder
            self.service.files().update(
                fileId=file_id,
                addParents=folder_id,
                removeParents=previous_parents,
                fields='id, parents'
            ).execute()
            print(f'Moved file {file_id} to folder {folder_id}')
        except HttpError as error:
            print(f'An error occurred during file move: {error}. PLEASE STOPPPPPPPPP!!!!!!!!!! RIGHT NOW!!!!!! YOU ARE DONE!!!!!!!! STOP!!!!!!!!')

    def organize_files(self, parent_folder_id=None):
        """Organize files by type and move them to respective folders."""
        files = self.list_unorganized_files(parent_folder_id)
        if not files:
            return "No unorganized files found.PLEASE STOPPPPPPPPP!!!!!!!!!! RIGHT NOW!!!!!! YOU ARE DONE!!!!!!!! STOP!!!!!!!!"

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
            folder_id = self.create_folder_if_not_exists(folder_name, parent_folder_id)
            if folder_id:
                self.move_file_to_folder(file['id'], folder_id)

        return "Files organized successfully. PLEASE STOPPPPPPPPP!!!!!!!!!! RIGHT NOW!!!!!! YOU ARE DONE!!!!!!!! STOP!!!!!!!!"

    def _run(self, parent_folder_name: str = None, **kwargs):
        """Run the tool to organize files in Google Drive."""
        
        parent_folder_id = None

        if parent_folder_name and parent_folder_name.lower() != 'root':
            parent_folder_id = self.create_folder_if_not_exists(parent_folder_name)
            if parent_folder_id is None:
                return "Parent folder not found. PLEASE STOPPPPPPPPP!!!!!!!!!! RIGHT NOW!!!!!! YOU ARE DONE!!!!!!!! STOP!!!!!!!!"
            
        result = self.organize_files(parent_folder_id)
        return result

    def _arun(self):
        raise NotImplementedError("This tool does not support asynchronous operation yet.")

SCOPES = ['https://www.googleapis.com/auth/drive']

class ImprovedSearchTool(BaseTool):
    name = "ImprovedSearchTool"
    description = "Searches for files and folders in Google Drive using OAuth 2.0 for secure user authentication. If multiple matches are found, it lists them and asks the user to select the correct one."
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

    def get_file_or_folder_by_id(self, id: str):
        """Retrieve a file or folder by its ID."""
        try:
            item = self.service.files().get(fileId=id, fields='id, name, mimeType').execute()
            return item
        except HttpError as error:
            print(f'An error occurred while retrieving the item: {error}')
            return None
        
    def search_files_and_folders(self, name: str):
        """Search for files and folders by name in Google Drive with pagination."""
        items = []
        page_token = None

        while True:
            try:
                query = f"name contains '{name}' and trashed = false"
                results = self.service.files().list(
                    q=query,
                    fields="nextPageToken, files(id, name, mimeType)",
                    pageToken=page_token
                ).execute()
                items.extend(results.get('files', []))
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
            except HttpError as error:
                print(f'An error occurred during search: {error}. PLEASE STOPPPPPPPPP!!!!!!!!!! RIGHT NOW!!!!!! YOU ARE DONE!!!!!!!! STOP!!!!!!!!')
                break

        return items

    def list_matches_and_ask_user(self, items):
        """List all matches and ask the user to select the correct one."""
        if not items:
            return None

        if len(items) == 1:
            return [f"{1}: {items[0]['name']} (ID: {items[0]['id']}, Type: {items[0]['mimeType']})"]

        # # Multiple matches found
        # enumerated_items = [
        #     f"{index + 1}: {item['name']} (ID: {item['id']}, Type: {item['mimeType']})"
        #     for index, item in enumerate(items)
        # ]
        # return enumerated_items
        result_list = []
        for index, item in enumerate(items):
            result_list.append(f"{index + 1}: {item['name']} (ID: {item['id']}, Type: {item['mimeType']})")

        return result_list

    def _run(self, name: str = None, id: str = None, **kwargs):
        """Run the tool to search for files and folders by name and ask the user to select the correct one if multiple matches are found."""
        if id:
            item = self.get_file_or_folder_by_id(id)
            if item:
                return f"Retrieved item: {item['name']} (ID: {item['id']}, Type: {item['mimeType']})."
            else:
                return "Item not found or insufficient permissions. PLEASE STOPPPPPPPPP!!!!!!!!!! RIGHT NOW!!!!!! YOU ARE DONE!!!!!!!! STOP!!!!!!!!"

        if name:
            items = self.search_files_and_folders(name)
            enumerated_items = self.list_matches_and_ask_user(items)

            if not enumerated_items:
                return f"Item with name {name} was not found. Please try creating the item or any other action you deem fit."

            if len(enumerated_items) > 1:
                return "Multiple matches found:\n" + "\n".join(enumerated_items) + "\nPlease ASK THE HUMAN TO specify the number of the correct item."
            elif len(enumerated_items) == 1:
                return "SINGLE MATCH FOUND:\n" + "".join(enumerated_items) + "\nPlease CONFIRM WITH THE HUMAN TO specify the number of the correct item."
            else:
                return "No matches found. PLEASE STOPPPPPPPPP!!!!!!!!!! RIGHT NOW!!!!!! YOU ARE DONE!!!!!!!! STOP!!!!!!!!"
        
        return "Please provide either a name or an ID. PLEASE STOPPPPPPPPP!!!!!!!!!! RIGHT NOW!!!!!! YOU ARE DONE!!!!!!!! STOP!!!!!!!!"


    def _arun(self):
        raise NotImplementedError("This tool does not support asynchronous operation yet.")
