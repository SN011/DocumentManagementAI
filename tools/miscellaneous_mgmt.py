from tools.imports import *
from googleapiclient.http import MediaFileUpload
from tools.auth import authenticate
from tools.file_mgmt_tools import DriveDictUpdateTool

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
        self.creds = authenticate()
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
            res = DriveDictUpdateTool(self.credentials_path).update_with_new_item(file_id)
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


class GoogleSheetsUpdateTool(BaseTool):
    name = "GoogleSheetsUpdateTool"
    description = ("Appends rows to a specified range in a Google Sheets spreadsheet.")

    credentials_path: str = Field(..., description="Path to the credentials JSON file")

    class Config:
        extra = Extra.allow

    def __init__(self, credentials_path: str):
        super().__init__()
        self.credentials_path = credentials_path
        self.creds = authenticate()
        self.service = build('sheets', 'v4', credentials=self.creds)

    def read_file_content(self, file_path):
        with open(file_path, 'r') as file:
            content = file.read().strip()
        return content

    def append_row_to_google_sheets(self, spreadsheet_id, range_name, values):
        """Appends rows to the specified range in the Google Sheets spreadsheet."""
        sheet = self.service.spreadsheets()
        body = {'values': values}
        result = sheet.values().append(
            spreadsheetId=spreadsheet_id, range=range_name,
            valueInputOption="RAW", body=body,
            insertDataOption="INSERT_ROWS"
        ).execute()
        print(f"{result.get('updates').get('updatedCells')} cells appended.")

    def _run(self, spreadsheet_name: str = None, spreadsheet_id: str = None, values: list = None, range_name: str = 'Sheet1', **kwargs):
        """Run the tool to append rows with the provided values to the specified range."""
        if not spreadsheet_id:
            return f"Use ImprovedSearchTool to find ID for the file (spreadsheet) by name {spreadsheet_name}, and pass it as an argument to this tool under 'spreadsheet_id' parameter. Be sure to pass in the spreadsheet_name as well."
        else:
            self.append_row_to_google_sheets(spreadsheet_id, range_name, values)
        return "Rows appended successfully. YOU ARE DONE APPENDING ROWS TO THE SHEET!! THE TOOL HAS EXECUTED SUCCESSFULLY!!!!!!!"

    def _arun(self, spreadsheet_id: str, values: list, range_name: str = 'Sheet1'):
        raise NotImplementedError("This tool does not support asynchronous operation yet.")
    
    
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
from tools.file_mgmt_tools import ImprovedSearchTool
class GoogleSheetsCreateTool(BaseTool):
    name = "GoogleSheetsCreateTool"
    description = ("Creates a new Google Sheets spreadsheet with specified column headers.")

    credentials_path: str = Field(..., description="Path to the credentials JSON file")

    class Config:
        extra = Extra.allow
        
    def __init__(self, credentials_path: str):
        super().__init__()
        self.credentials_path = credentials_path
        self.creds = authenticate()
        self.service = build('sheets', 'v4', credentials=self.creds)
        self.IST = ImprovedSearchTool(credentials_path=self.credentials_path)

    def create_google_sheet(self, title, headers):
        """Creates a new Google Sheets spreadsheet with the specified title and headers."""
        
        
        sheet = self.service.spreadsheets()
        spreadsheet = {
            'properties': {
                'title': title
            },
            'sheets': [
                {
                    'data': [
                        {
                            'startRow': 0,
                            'startColumn': 0,
                            'rowData': [
                                {
                                    'values': [{'userEnteredValue': {'stringValue': header}} for header in headers]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        result = sheet.create(body=spreadsheet).execute()
        spreadsheet_id = result.get('spreadsheetId')
        print(f"Spreadsheet ID: {spreadsheet_id}")
        return spreadsheet_id

  
    
    def _run(self, title: str, headers: list, **kwargs):
        """Run the tool to create a new Google Sheet with the specified title and headers."""
        
        result = self.IST._run(name=title)
        if 'single' in result.lower() or 'multiple' in result.lower():
            return result
        spreadsheet_id = self.create_google_sheet(title, headers)
        res = DriveDictUpdateTool(self.credentials_path).update_with_new_item(spreadsheet_id)
        return f"Spreadsheet created successfully with ID: {spreadsheet_id}. IF PREVIOUSLY INSTRUCTED TO POPULATE DATA, USE GOOGLE SHEETS UPDATE TOOL!! THIS TOOL (GOOGLE SHEETS CREATE TOOL) DOES NOT TAKE ANY VALUES. IT ONLY INPUTS THE HEADERS INTO THE SHEET!!!!"

    def _arun(self, title: str, headers: list):
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
        self.creds = authenticate()
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
            try:
                with open(pdf_path, 'rb') as file:
                    part.set_payload(file.read())
            except: 
                return "INVALID FILE PATH. WHATEVER YOU HAVE INPUTTED IS A WRONG PATH. PATH MEANS A FILE PATH ON THE LOCAL MACHINE/COMPUTER."
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
            return f'An error occurred: {error}'

    def _run(self, sender_email: str, recipient_email: str, subject: str, body: str, pdf_path: str = None, **kwargs):
        """Run the tool to send the email with the optional PDF attachment."""
        result = self.send_email(sender_email, recipient_email, subject, body, pdf_path)
        return f"Email sent successfully with message ID {result["id"]}. YOU ARE DONNNNEEEEEEEEEEEEE!!!!!!!! TOOL EXECUTED SUCCESSFULLY!!!!!!!!!!!!!" if result else "Failed to send email."

    def _arun(self):
        raise NotImplementedError("This tool does not support asynchronous operation yet.")



    
    


