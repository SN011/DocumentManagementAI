from tools.imports import *
import tools.initialize_groq
client,_ = tools.initialize_groq.init_groq()

DOCUMENT_IDS_FILE = "document_ids.txt"
SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']

def make_docmgr_write_to_file(cc_out):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": """You are a detailed and professional assistant. Your task is to generate comprehensive and detailed formatted text. 
                Ensure everything is included !!!!! DO NOT DO NOT DO NOTTTTTTT summarize or truncate any content. OR ELSE I WILL GET REALLY MAD YOU MUST INCLUDE EVERYTHING INCLUDE EVERYTHHIINGNGNGNGNGNGNGGGG!!!!!!!
                Your response must be well-formed and include all details. 

                You must ALWAYS ALWAYS ALWAYS!!!!! output in a structured format as follows AND NO QUOTATION MARKS OR BACKSLASHES!:
                
                            
                {
                    "title": "The Great Renovation",
                    "sections": [
                        {
                            "content": "<specific text content>",
                            "font_name": "<font family>",
                            "font_size": <integer specifying font size>,
                            "bold": <true or false>,
                            "italic": <true or false>,
                            "alignment": "<right, left, justify or center>"
                            "color": [<integer for red>, <integer for green>, <integer for blue>]
                        },
                        {
                            "content": "<another specific text content>",
                            "font_name": "<another font family>",
                            "font_size": <another integer specifying font size>,
                            "bold": <true or false>,
                            "italic": <true or false>,
                            "alignment": "<right, left, justify or center>"
                            "color": [<integer for red>, <integer for green>, <integer for blue>]
                        }
                        // ... more sections as needed
                    ],
                    "append": <true or false> (this indicates appending to document or not)
                }
                PLEASE! Ensure the output is well-formed and valid."""
            },
            {
                "role": "user",
                "content": "Give whatever file title you want;NO COLONS!ONLY HYPHENS!. Please Include a new title IN THE DOCUMENT, headings if you deem fit, and please format in a nice readable and coherent way.  \
                    Specify the formatting for this text. Please make it a \
                        PROFESSIONALLY formatted text WITH black & blue colors and times new roman font PLEASE. NO NO NO bullet points of ANY KIND unless specified: " + cc_out
            }
        ],
        model="llama3-70b-8192",
    )

    cc_out2 = chat_completion.choices[0].message.content

    print('CCOUT2\n',cc_out2)

    return cc_out2

def authenticate(credentials_path):
    """Authenticate the user with Google Drive API using OAuth 2.0."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

# Initialize credentials and API clients
credentials_path = "C:\\DEV\\WebdevFolder\\client_secret_291175256673-gr5p5vf3pi2h0m46h5qnd3ila4iitfqs.apps.googleusercontent.com.json"
creds = authenticate(credentials_path)
docs_service = build('docs', 'v1', credentials=creds)
drive_service = build('drive', 'v3', credentials=creds)

def create_google_doc(title):
    body = {
        'title': title
    }
    doc = docs_service.documents().create(body=body).execute()
    with open(DOCUMENT_IDS_FILE,'w') as difile:
        difile.write(doc['documentId'])
    return doc['documentId']

def share_document_with_user(document_id, user_email):
    permission = {
        'type': 'user',
        'role': 'writer',
        'emailAddress': user_email
    }
    try:
        drive_service.permissions().create(
            fileId=document_id,
            body=permission,
            fields='id'
        ).execute()
        print(f'Document shared with {user_email}')
    except googleapiclient.errors.HttpError as error:
        print(f'An error occurred: {error}')
        if 'User message' in error.resp.reason:
            print(error.resp['User message'])

def get_document_end_index(document_id):
    doc = docs_service.documents().get(documentId=document_id).execute()
    content = doc.get('body').get('content')
    print(f'Document content: {content}')  # Debug print
    end_index = content[-1]['endIndex'] if content else 1
    print(f'Document end index: {end_index}')  # Debug print
    return end_index


def append_text_with_formatting(document_id, text, font_name, font_size, bold, italic, alignment, color, start_index):
    if not text.strip():
        return start_index  # Skip empty text

    # Ensure the start index is within valid bounds
    start_index = max(1, start_index - 1)

    # Debug print for start_index and text
    print(f'Appending text starting at index: {start_index}')
    print(f'Text to append: {text}')

    requests = [
        {
            'insertText': {
                'location': {
                    'index': start_index,
                },
                'text': text
            }
        }
    ]
    text_style = {
        'fontSize': {
            'magnitude': font_size,
            'unit': 'PT'
        },
        'weightedFontFamily': {
            'fontFamily': font_name
        },
        'bold': bold,
        'italic': italic,
        'foregroundColor': {
            'color': {
                'rgbColor': {
                    'red': color[0] / 255.0,
                    'green': color[1] / 255.0,
                    'blue': color[2] / 255.0
                }
            }
        }
    }
    requests.append({
        'updateTextStyle': {
            'range': {
                'startIndex': start_index,
                'endIndex': start_index + len(text)
            },
            'textStyle': text_style,
            'fields': 'foregroundColor,bold,italic,fontSize,weightedFontFamily'
        }
    })

    alignment_mapping = {
        "left": "START",
        "center": "CENTER",
        "right": "END",
        "justify": "JUSTIFIED"
    }

    if alignment.lower() in alignment_mapping:
        google_alignment = alignment_mapping[alignment.lower()]
        requests.append({
            'updateParagraphStyle': {
                'range': {
                    'startIndex': start_index,
                    'endIndex': start_index + len(text)
                },
                'paragraphStyle': {
                    'alignment': google_alignment
                },
                'fields': 'alignment'
            }
        })

    try:
        # Execute the batchUpdate request
        response = docs_service.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()
        print(f'Batch update response: {response}')  # Debug print
    except HttpError as error:
        print(f'An error occurred during batchUpdate: {error}')
        raise  # Re-raise the error to be caught by the calling function

    return start_index + len(text)

def write_to_google_doc(document_id, sections, append):
    start_index = get_document_end_index(document_id) if append else 1
    print(f'Start index: {start_index}')  # Debug print
    for section in sections:
        start_index = append_text_with_formatting(
            document_id,
            section['content'] + "\n\n",
            section.get('font_name', 'Times New Roman'),
            section.get('font_size', 12),
            section.get('bold', False),
            section.get('italic', False),
            section.get('alignment', 'left'),
            section.get('color', [0, 0, 0]),
            start_index
        )
        print(f'New start index: {start_index}')  # Debug print
        time.sleep(1)
    print(f'Finished writing to document ID: {document_id}')  # Debug print


def parse_formatted_response(response):
    title_match = re.search(r'"title":\s*"([^"]+)"', response)
    title = title_match.group(1) if title_match else "Untitled Document"
    
    sections_matches = re.findall(r'\{([^}]+)\}', response)
    sections = []
    for match in sections_matches:
        section = {}
        content_match = re.search(r'"content":\s*"([^"]+)"', match)
        font_name_match = re.search(r'"font_name":\s*"([^"]+)"', match)
        font_size_match = re.search(r'"font_size":\s*(\d+)', match)
        bold_match = re.search(r'"bold":\s*(true|false)', match)
        italic_match = re.search(r'"italic":\s*(true|false)', match)
        alignment_match = re.search(r'"alignment":\s*"([^"]+)"', match)
        color_match = re.search(r'"color":\s*\[(\d+),\s*(\d+),\s*(\d+)\]', match)
        
        if content_match:
            content = content_match.group(1)
            # Replace double quotes indicating inches with the word "inch"
            content = re.sub(r'(?<=\d)"', ' inch', content)
            section["content"] = content
        else:
            section["content"] = ""
        
        section["font_name"] = font_name_match.group(1) if font_name_match else "Arial"
        section["font_size"] = int(font_size_match.group(1)) if font_size_match else 12
        section["bold"] = bold_match.group(1) == "true" if bold_match else False
        section["italic"] = italic_match.group(1) == "true" if italic_match else False
        section["alignment"] = alignment_match.group(1) if alignment_match else "left"
        if color_match:
            section["color"] = (int(color_match.group(1)), int(color_match.group(2)), int(color_match.group(3)))
        
        sections.append(section)
    
    append_match = re.search(r'"append":\s*(true|false)', response)
    append = append_match.group(1) == "true" if append_match else False
    
    return title, sections, append

def search_document_by_name(name):
    query = f"name = '{name}' and mimeType = 'application/vnd.google-apps.document' and trashed = false"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get('files', [])
    return items

class GoogleDocWriteTool(BaseTool):
    def __init__(self):
        super().__init__(name="GoogleDocWriteTool", description="Writes any amount of content to a Google Doc with professional formatting")

    def _run(self, input_text, user_email, append=False, document_name=None):
        try:
            # Parse the input text
            processed_input = make_docmgr_write_to_file(input_text)
            title, sections, append_response = parse_formatted_response(processed_input)
            append = append or append_response

            # Search for the document by name
            if document_name:
                documents = search_document_by_name(document_name)
                if documents:
                    document_id = documents[0]['id']
                    print(f'Found existing document with ID: {document_id}')
                else:
                    document_id = create_google_doc(document_name)
                    print(f'Document created with ID: {document_id}')
            else:
                document_id = create_google_doc(title)
                print(f'Document created with ID: {document_id}')

            # Share the document with the user's email
            print(f'Sharing document with ID: {document_id} with {user_email}')  # Debug print
            share_document_with_user(document_id, user_email)
            print(f'Document shared with {user_email}')  # Debug print

            # Write the content to the Google Doc
            print(f'Writing content to document ID: {document_id}')  # Debug print
            write_to_google_doc(document_id, sections, append)
            print(f'Content written to document ID: {document_id}')  # Debug print

            # Return the URL to access the document
            document_url = f'https://docs.google.com/document/d/{document_id}/edit'
            print(f'Access the document at: {document_url}')
            return "THE CONTENT HAS BEEN WRITTEN!!!!!!!! PLEASE STOP!!!!!!!! YOURE DONE!!!!!!!!! NO MORE!!!!"
        except HttpError as error:
            print(f'An error occurred: {error}')
            return f"An error occurred: {error}"
