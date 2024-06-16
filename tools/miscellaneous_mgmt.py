from tools.imports import *

class GoogleDriveUploadTool(BaseTool):
    name = "GoogleDriveUploadTool"
    description = ("Uploads a PDF to Google Drive and sets permissions for a specific user. "
                   "Please set the 'rename' parameter to None if the user does not want to rename the file before uploading "
                   "to Google Drive. STOP AFTER ONE-TIME SUCCESSFUL EXECUTION")

    def _run(self, file_path: str, user_email: str, rename: str) -> str:
        #credentials_path = "C:\Users\THEBATMAN\Documents\GitHub\RealEstateAI\filemanager-425819-341d30387005.json"
        credentials_path = "C:\\DEV\\WebdevFolder\\realestateai-doc-mgr-3a0e2f411c8d.json"
        # Authenticate and create the service
        try:
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            service = build('drive', 'v3', credentials=credentials)
            print("Successfully authenticated and created the service.")
        except google.auth.exceptions.GoogleAuthError as e:
            return f"Authentication error: {e}"

        # File details
        if rename is not None:
            file_metadata = {'name': rename}
        else:
            file_metadata = {'name': os.path.basename(file_path)}

        if not os.path.exists(file_path):
            return f"File not found: {file_path}"
        else:
            media = MediaFileUpload(file_path, mimetype='application/pdf')
            try:
                # Upload file
                file = service.files().create(body=file_metadata, media_body=media, fields='id, name, parents').execute()
                file_id = file.get('id')
                with open('file_id_history.txt','w') as id_hist_file:
                    id_hist_file.write(file_id)
                print(f"File ID: {file_id}")

                # Verify the upload by fetching the file details
                file_info = service.files().get(fileId=file_id, fields='id, name, parents').execute()
                print("File details:")
                print(file_info)

                # Sharing settings
                permission = {
                    'type': 'user',
                    'role': 'writer',  # Set to 'reader' if read-only access is needed
                    'emailAddress': user_email,
                    
                }
                

                # Grant permission to the specific user
                try:
                    service.permissions().create(
                        fileId=file_id,
                        body=permission,
                        fields='id',
                        sendNotificationEmail=False
                    ).execute()
                    
                    print(f"Granted {permission['role']} access to {user_email}")
                    
                    

                except googleapiclient.errors.HttpError as e:
                    print(f"Error setting permission: {e}")
                    return f"Error setting permission: {e}"

                return f"File uploaded and permissions set successfully. File ID: {file_id}. PLEASE STOP WORKING! THE TOOL HAS BEEN EXECUTED PROPERLY!" 

            except Exception as e:
                return f"Error during file upload or conversion: {e}"

    

    def _arun(self, file_path: str, user_email: str, rename: str):
        raise NotImplementedError("This tool does not support asynchronous operation yet.")

# Example usage
# tool = GoogleDriveUploadTool()
# response = tool._run(file_path='./documents/The Great Renovation.pdf', user_email='specific-user@example.com', rename=None)
# print(response)




class GoogleSheetsUpdateTool(BaseTool):
    name = "GoogleSheetsUpdateTool"
    description = ("Appends three columns - name, phone number, and link to a PDF - to a preexisting logging google sheet. STOP AFTER ONE-TIME SUCCESSFUL EXECUTION")
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    #credentials_path = 'C:\Users\THEBATMAN\Documents\GitHub\RealEstateAI\filemanager-425819-341d30387005.json'
    credentials_path = "C:\\DEV\\WebdevFolder\\realestateai-doc-mgr-3a0e2f411c8d.json"
    spreadsheet_id = '1TSFyiTwctC1tABr2RQouBzLRMCG4RZ7lXdTVi-I58Mo'
    range_name = 'Sheet1'
    
    #creds = authenticate_google_sheets()
    
    def authenticate_google_sheets(self):
        creds = service_account.Credentials.from_service_account_file(
            self.credentials_path, scopes=self.SCOPES)
        return creds
    
    def read_file_content(self, file_path):
        with open(file_path, 'r') as file:
            content = file.read().strip()
        return content
    
    
    def append_row_to_google_sheets(self, values):
        """
        Appends a row to the specified range in the Google Sheets spreadsheet.
        
        :param values: The data to append, as a list of lists (e.g., [['A1', 'B1', 'C1']]).
        """
        service = build('sheets', 'v4', credentials=self.authenticate_google_sheets())
        sheet = service.spreadsheets()
        body = {'values': values}
        result = sheet.values().append(
            spreadsheetId=self.spreadsheet_id, range=self.range_name,
            valueInputOption="RAW", body=body,
            insertDataOption="INSERT_ROWS"
        ).execute()
        print(f"{result.get('updates').get('updatedCells')} cells appended.")

    def _run(self, name: str, phone_number: str, linkstr:str):
        """
        Run the tool to append the row with the given name, phone number, and link to the PDF.
        
        :param name: The full legal name to append.
        :param phone_number: The phone number to append.
        """
        fileID = self.read_file_content('file_id_history.txt')
        
        print(f"Extracted file ID: {fileID}")
        link = f"https://drive.google.com/file/d/{fileID}/view"
        values = [[]]
        if linkstr:
            values = [[name, phone_number, linkstr]]
        else:
            values = [[name, phone_number, link]]
        self.append_row_to_google_sheets(values)
        return "Row appended successfully. YOU ARE DONNNNEEEEEEEEEEEEE!!!!!!!! TOOL EXECUTED SUCCESSFULLY!!!!!!!!!!!!!"

    def _arun(self, name: str, phone_number: str):
        raise NotImplementedError("This tool does not support asynchronous operation yet.")
    


# If modifying these SCOPES, delete the file token.json.
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

    def authenticate(self):
        """Authenticate the user with Gmail API."""
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
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

    def _run(self, sender_email: str, recipient_email: str, subject: str, body: str, pdf_path: str = None):
        """Run the tool to send the email with the optional PDF attachment."""
        result = self.send_email(sender_email, recipient_email, subject, body, pdf_path)
        return "Email sent successfully. YOU ARE DONNNNEEEEEEEEEEEEE!!!!!!!! TOOL EXECUTED SUCCESSFULLY!!!!!!!!!!!!!" if result else "Failed to send email."

    def _arun(self):
        raise NotImplementedError("This tool does not support asynchronous operation yet.")
    


