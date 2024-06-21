from tools.imports import *
from googleapiclient.http import MediaFileUpload



class GoogleDriveUploadTool(BaseTool):
    name = "GoogleDriveUploadTool"
    description = ("Uploads a PDF to Google Drive and sets permissions for a specific user. "
                   "Please set the 'rename' parameter to None if the user does not want to rename the file before uploading "
                   "to Google Drive. STOP AFTER ONE-TIME SUCCESSFUL EXECUTION")

    credentials_path: str = Field(..., description="Path to the credentials JSON file")
    
    class Config:
        extra = Extra.allow

    def __init__(self, credentials_path: str):
        super().__init__()
        self.credentials_path = credentials_path
        self.creds = None
        self.authenticate()

    def authenticate(self):
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, ['https://www.googleapis.com/auth/drive'])
                self.creds = flow.run_local_server(port=0)
        self.service = build('drive', 'v3', credentials=self.creds)

    def upload_file(self, file_path: str, user_email: str, rename: str = None):
        """Upload a file to Google Drive and set permissions."""
        file_metadata = {'name': rename if rename else os.path.basename(file_path)}

        if not os.path.exists(file_path):
            return f"File not found in the LOCAL SYSTEM: {file_path}"
        
        mime_type, _ = mimetypes.guess_type(file_path)
        print('THE MIMETYPE MIGHT BE: ', mime_type)
        if mime_type is None:
            mime_type = 'application/octet-stream'  # Default MIME type if unknown

        media = MediaFileUpload(file_path, mimetype=mime_type)
        try:
            file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            file_id = file.get('id')
            with open('file_id_history.txt', 'w') as id_hist_file:
                id_hist_file.write(file_id)
            print(f"File ID: {file_id}")

            # permission = {
            #     'type': 'user',
            #     'role': 'writer',
            #     'emailAddress': user_email,
            # }

            # try:
            #     self.service.permissions().create(
            #         fileId=file_id,
            #         body=permission,
            #         fields='id',
            #         sendNotificationEmail=False
            #     ).execute()
            #     print(f"Granted {permission['role']} access to {user_email}")
            # except Exception as e:
            #     print(f"Error setting permission: {e}")
            #     return f"Error setting permission: {e}"

            return f"File uploaded successfully. File ID: {file_id}. PLEASE STOP WORKING! THE TOOL HAS BEEN EXECUTED PROPERLY!"
        except Exception as e:
            return f"Error during file upload or conversion: {e}"

    def _run(self, file_path: str, user_email: str, rename: str = None):
        """Run the tool to upload the file to Google Drive and set permissions."""
        result = self.upload_file(file_path, user_email, rename)
        return result

    def _arun(self, file_path: str, user_email: str, rename: str = None):
        raise NotImplementedError("This tool does not support asynchronous operation yet.")


SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

class GoogleSheetsUpdateTool(BaseTool):
    name = "GoogleSheetsUpdateTool"
    description = ("Appends three columns - name, phone number, and link to a PDF - to a preexisting logging google sheet. STOP AFTER ONE-TIME SUCCESSFUL EXECUTION")

    credentials_path: str = Field(..., description="Path to the credentials JSON file")
    spreadsheet_id: str = Field(default="1TSFyiTwctC1tABr2RQouBzLRMCG4RZ7lXdTVi-I58Mo", description="Google Sheets spreadsheet ID")
    range_name: str = Field(default="Sheet1", description="Range in the spreadsheet to append data to")

    class Config:
        extra = Extra.allow

    def __init__(self, credentials_path: str, spreadsheet_id: str = "1TSFyiTwctC1tABr2RQouBzLRMCG4RZ7lXdTVi-I58Mo", range_name: str = 'Sheet1'):
        super().__init__()
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.range_name = range_name
        self.creds = None
        self.service = None
        self.authenticate()

    def authenticate(self):
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, ['https://www.googleapis.com/auth/spreadsheets'])
                self.creds = flow.run_local_server(port=0)
        self.service = build('sheets', 'v4', credentials=self.creds)

    def read_file_content(self, file_path):
        with open(file_path, 'r') as file:
            content = file.read().strip()
        return content

    def append_row_to_google_sheets(self, values):
        """Appends a row to the specified range in the Google Sheets spreadsheet."""
        
        sheet = self.service.spreadsheets()
        body = {'values': values}
        result = sheet.values().append(
            spreadsheetId=self.spreadsheet_id, range=self.range_name,
            valueInputOption="RAW", body=body,
            insertDataOption="INSERT_ROWS"
        ).execute()
        print(f"{result.get('updates').get('updatedCells')} cells appended.")

    def _run(self, name: str, phone_number: str, linkstr: str = None, otherlinkstr:str=None):
        """Run the tool to append the row with the given name, phone number, and link to the PDF."""
        fileID = self.read_file_content('file_id_history.txt')
        print(f"Extracted file ID: {fileID}")
        link = f"https://drive.google.com/file/d/{fileID}/view"
        values = [[name, phone_number, linkstr or link, otherlinkstr]]
        self.append_row_to_google_sheets(values)
        return "Row appended successfully. YOU ARE DONNNNEEEEEEEEEEEEE!!!!!!!! TOOL EXECUTED SUCCESSFULLY!!!!!!!!!!!!!"

    def _arun(self, name: str, phone_number: str):
        raise NotImplementedError("This tool does not support asynchronous operation yet.")
    
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

class GmailSendPdfTool(BaseTool):
    name = "GmailSendPdfTool"
    description = "Sends an email with an optional PDF attachment using Gmail API."

    credentials_path: str = Field(..., description="Path to the credentials JSON file")

    class Config:
        extra = Extra.allow

    def __init__(self, credentials_path: str):
        super().__init__()
        self.credentials_path = credentials_path
        self.creds = None
        self.service = None
        self.authenticate()

    # def authenticate(self):
    #     """Authenticate the user with Google Drive API using OAuth 2.0."""
    #     if os.path.exists('token.json'):
    #         self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    #     if not self.creds or not self.creds.valid:
    #         if self.creds and self.creds.expired and self.creds.refresh_token:
    #             self.creds.refresh(Request())
    #         else:
    #             flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
    #             self.creds = flow.run_local_server(port=0)
    #         with open('token.json', 'w') as token:
    #             token.write(self.creds.to_json())
    #     self.service = build('gmail', 'v1', credentials=self.creds)
    def authenticate(self):
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, ['https://www.googleapis.com/auth/gmail.send'])
                self.creds = flow.run_local_server(port=0)
            
        self.service = build('gmail', 'v1', credentials=self.creds)

    def send_email(self, sender_email, recipient_email, subject, body, pdf_path=None):
        """Send an email with an optional PDF attachment."""
        message = MIMEMultipart()
        message['to'] = recipient_email
        message['from'] = sender_email
        message['subject'] = subject
        body_part = MIMEText(body, 'plain')
        message.attach(body_part)
        
        if pdf_path:
            part = MIMEBase('application', 'octet-stream')
            with open(pdf_path, 'rb') as file:
                part.set_payload(file.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(pdf_path)}"')
            message.attach(part)
       
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        raw_message = {'raw': raw_message}

        try:
            message = (self.service.users().messages().send(userId="me", body=raw_message).execute())
            print(f'Message Id: {message["id"]}')
            return message
        except HttpError as error:
            print(f'An error occurred: {error}')
            return None

    def _run(self, sender_email: str, recipient_email: str, subject: str, body: str, pdf_path: str = None, **kwargs):
        """Run the tool to send the email with the optional PDF attachment."""
        result = self.send_email(sender_email, recipient_email, subject, body, pdf_path)
        return "Email sent successfully. YOU ARE DONNNNEEEEEEEEEEEEE!!!!!!!! TOOL EXECUTED SUCCESSFULLY!!!!!!!!!!!!!" if result else "Failed to send email."

    def _arun(self):
        raise NotImplementedError("This tool does not support asynchronous operation yet.")



    
    


