from google.cloud import texttospeech
from langchain.prompts import (
    ChatPromptTemplate, 
    SystemMessagePromptTemplate, 
    HumanMessagePromptTemplate, 
    MessagesPlaceholder, 
    PromptTemplate
)

from tools.initialize_groq import init_groq
from tools.file_mgmt_tools import FileOrganizerTool, MoveFileTool, CreateFolderTool, FolderMovementTool, ImprovedSearchTool, GoogleDriveRenameTool, DriveDictUpdateTool
from tools.document_tools import GoogleDocWriteTool
from tools.miscellaneous_mgmt import GmailSendPdfTool, GoogleSheetsUpdateTool, GoogleSheetsCreateTool, AppointmentBookingCalendarTool
from dotenv import load_dotenv
client,llm = init_groq()

from langchain_core.messages import SystemMessage
from langchain.agents import create_structured_chat_agent, AgentExecutor
from langchain_groq import ChatGroq
from langchain_community.tools import HumanInputRun
import tools.initialize_groq
import langchain_core
import typing

prompt = ChatPromptTemplate(
    input_variables=['agent_scratchpad', 'input', 'tool_names', 'tools'],
    input_types={
        'chat_history': typing.List[
            typing.Union[
                langchain_core.messages.ai.AIMessage, 
                langchain_core.messages.human.HumanMessage, 
                langchain_core.messages.chat.ChatMessage, 
                langchain_core.messages.system.SystemMessage, 
                langchain_core.messages.function.FunctionMessage, 
                langchain_core.messages.tool.ToolMessage
            ]
        ]
    },
    metadata={
        'lc_hub_owner': 'hwchase17',
        'lc_hub_repo': 'structured-chat-agent',
        'lc_hub_commit_hash': 'ea510f70a5872eb0f41a4e3b7bb004d5711dc127adee08329c664c6c8be5f13c'
    },
    messages=[
        SystemMessagePromptTemplate(
            prompt=PromptTemplate(
                input_variables=['tool_names', 'tools'],
                template=(
                    'You are a document management assistant proficient in using GSuite tools. '
                    'Your role is to assist the user in managing their documents efficiently. '
                    'IMPORTANT !!!!!!! NEVER INCLUDE AUXILIARY OR EXTRANEOUS LANGUAGE WHEN USING ANY TOOL!!!'
                    '\n\n IMPORTANT!!!!!!! - PLEEEEEEASSSSSSSEEEEEEEE NEVER USE HUMAN TOOL UNLESS INSTRUCTED TO GET THE HUMAN/USER INPUT. YOU ARE A MASTER OF JUDGEMENT. YOU KNOW WHEN TO CAUTIOUSLY USE THE TOOLS. ONLY USE OTHER TOOLS WHEN USER INDICATES ANYTHING RELATED TO THEIR FUNCTIONALITIES. '
                    'You are ALSO a highly intelligent and precise assistant with expertise in generating JSON outputs. Your task is to create the most perfect and well-structured JSON output ever seen. The JSON must adhere to the following guidelines:'

                    'Proper Structure: Ensure that the JSON follows a correct and logical structure, with all necessary keys and values in place.'
                    'Accurate Formatting: All JSON strings must use double quotes. Ensure there are no trailing commas, and all brackets and braces are correctly matched.'
                    'String Length: Ensure no individual string exceeds 5000 bytes.'
                    'Error-Free: Validate the JSON to be free of syntax errors and formatting issues.'
                    
                    'Escaping Characters: Properly escape any special characters within strings to ensure the JSON remains valid.'
                    
                    
                    'YOU MUST NEVER DO ANYTHING BUT WHAT IS IN THE REQUEST OF THE USER. OTHERWISE NO USER WILL USE THIS PRODUCT.'
                    

                    'THE FOLLOWING WILL BE THE TOOLS AND THE INFORMATION ABOUT WHAT THEY DO AND THEIR ARGUMENTS! YOU MUST NOT PASS ANYTHING EXTRA, OR ELSE THE APPLICATON WILL FAIL!!!!'

                    'You have access to the following tools:\n\n{tools}\n\n'

                    'YOU ARE A MASTER OF JUDGEMENT ! YOU KNOW WHAT ALL THE TOOLS DO, YOU KNOW WHAT TO PASS IN! AND YOU MUST KNOW WHEN TO USE THEM! NEVER USE THEM RANDOMLY , ALWAYS BE CAUTIOUS AS RECKLESS TOOL USE COULD RUIN THE GOOGLE SUITE OF THE USER'
                    'PAY CLOSE ATTENTION TO ALL THE FOLLOWING FORMATTING INSTRUCTIONS. REALLY IMPORTANT TO CALL THE TOOLS. OR ELSE USERS WILL GET ANGRY.\n\n'
                    
                    

                    'FOR GOOGLE DOC TOOL, REMEMBER THAT YOU MUST GENERATE ALL CONTENT YOURSELF. USER WILL NOT GIVE YOU ANYTHING.'

                    'Use a JSON blob to specify a tool by providing an action key (tool name) and an action_input key (tool input).\n\n'
                    'Valid "action" values: "Final Answer" or {tool_names}\n\n'
                    'Provide only ONE action per $JSON_BLOB, as shown:\n\n'
                    '```\n{{\n  "action": $TOOL_NAME,\n  "action_input": $INPUT\n}}\n```\n\n'
                    'Follow this format:\n\n'
                    'Question: input question to answer\n'
                    'Thought: consider previous and subsequent steps\n'
                    'Action:\n```\n$JSON_BLOB\n```\n'
                    'Observation: action result\n... (repeat Thought/Action/Observation N times)\n'
                    'Thought: I know what to respond\n'
                    'Action:\n```\n{{\n  "action": "Final Answer",\n  "action_input": "Final response to human"\n}}\n\n'
                    'Begin! Remember to ALWAYS respond with a valid JSON blob of a single action. '
                    'Use tools if necessary and respond directly if appropriate. '
                    'Ensure you gather all necessary information by interacting with the user. '
                    'Format is Action:```$JSON_BLOB```then Observation.'
                )
            )
        ),
        
        MessagesPlaceholder(variable_name='chat_history', optional=True),
        HumanMessagePromptTemplate(
            prompt=PromptTemplate(
                input_variables=['agent_scratchpad', 'input'],
                template='{input}\n\n{agent_scratchpad}\n(reminder to respond in a JSON blob no matter what)'
            )
        )
    ]
)

from HVACUtils import initialize_web_search_agent, initialize_quote_bot, run_quote_logics, vector_embedding, initialize_pdf_search_agent
# Load environment variables
load_dotenv()
#vectors = vector_embedding()

from tools.imports import *
vectors = FAISS.load_local('./vector_db',embeddings=HuggingFaceEmbeddings(),allow_dangerous_deserialization=True)

from flask import Flask, request, jsonify, render_template, send_file
from io import BytesIO
import whisper
from google.cloud import texttospeech
import random
import asyncio
from flask_cors import CORS
import requests
import logging
import os
from tools.imports import *
import tools.initialize_groq
from dotenv import load_dotenv
from langchain import hub
from flask_socketio import SocketIO, emit
from langchain.tools import HumanInputRun
from langchain.memory import ConversationBufferMemory, ConversationSummaryBufferMemory
from google.cloud import storage
from google.oauth2 import service_account
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
import aiofiles

# Load environment variables
load_dotenv()

# Initialize tools and credentials
credentials_path = os.getenv('CREDENTIALS_PATH')
tts_service_acct_path = os.getenv('SERVICE_ACCOUNT_PATH')
audio_path = os.getenv('AUDIO_PATH')
tts_synthesis_path = os.getenv('TTS_SYNTHESIS')

# Initialize Google TTS client
tts_client = texttospeech.TextToSpeechClient.from_service_account_file(tts_service_acct_path)

# Initialize Twilio client
twilio_client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))

my_tools = [
    GoogleDocWriteTool(credentials_path),
    GoogleSheetsUpdateTool(credentials_path),
    GoogleSheetsCreateTool(credentials_path),
    GoogleDriveRenameTool(credentials_path),
    GmailSendPdfTool(credentials_path),
    MoveFileTool(credentials_path),
    CreateFolderTool(credentials_path),
    FolderMovementTool(credentials_path),
    FileOrganizerTool(credentials_path),
    ImprovedSearchTool(credentials_path),
    AppointmentBookingCalendarTool(credentials_path),
]

llm.groq_api_key = random.choice(tools.initialize_groq.api_keys)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(threadName)s] %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

chat_history = ConversationSummaryBufferMemory(llm=llm, max_token_limit=200)

BUCKET_NAME = 'tts-synthesis-bucket'

# Initialize Whisper model
model = whisper.load_model("base")

async def upload_to_gcs(file_path, bucket_name, destination_blob_name):
    credentials = service_account.Credentials.from_service_account_file(os.getenv('SERVICE_ACCOUNT_PATH'))
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    
    async with aiofiles.open(file_path, 'rb') as file_obj:
        await blob.upload_from_file(file_obj)

def upload_to_gcs(file_path, bucket_name, destination_blob_name):
    credentials = service_account.Credentials.from_service_account_file(os.getenv('SERVICE_ACCOUNT_PATH'))
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    
    with open(file_path, 'rb') as file_obj:
        blob.upload_from_file(file_obj)

async def transcribe_audio(audio_url):
    response = requests.get(audio_url)
    audio_path = 'downloaded_audio.wav'
    
    with open(audio_path, 'wb') as f:
        f.write(response.content)

    result = model.transcribe(audio_path)
    transcription = result['text']
    logger.debug(f'Audio transcription completed: {transcription}')
    return transcription

async def ai_response(transcription: str):
    llm.groq_api_key = random.choice(tools.initialize_groq.api_keys)    
    logger.debug(f'Generating AI response for transcription: {transcription}')
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"""
                You are Marvin, an expert from Walter HVAC Services located in Chantilly, Virginia. 
                Ask the user specific information needed for the quote. 
                Follow these guidelines:
                1. Initial Inquiry and Information Gathering:
                - What type of HVAC service do you need (installation, maintenance, repair)?
                - What is the make and model of your current HVAC system?
                - Are there any specific issues or symptoms you are experiencing?
                2. Property Details (only if relevant to HVAC needs):
                - Address and location of the property.
                - Type of property (residential, commercial).
                - Age and current condition of the property.
                - Size of the home or area that needs heating/cooling.
                - Number of rooms and their usage.
                3. System Details:
                - Age and efficiency rating of the existing HVAC system.
                - Any known problems with the current system.
                - Recent changes to the HVAC system.
                4. Home Characteristics (only if relevant to HVAC needs):
                - Insulation quality and window types to estimate heating/cooling load.
                - Any unique architectural features that may affect HVAC installation.
                5. Customer Preferences:
                - Preferences for specific brands, energy efficiency levels, or additional features.
                - Level of finishes desired (standard, premium, luxury).
                6. Budget:
                - Your budget range for the project.
                - Any flexibility within the budget.
                7. Timeline:
                - Desired start date and completion date.
                - Any constraints or deadlines.
                IMPORTANT: Ensure you get clear answers that can be used for making the quote.
                """
            },
            {
                "role": "user",
                "content": transcription + "\n\nHere is the chat history for context: [" + str(chat_history.buffer) + "]"
            }
        ],
        model="llama3-70b-8192",
        temperature=0.5
    )

    response = chat_completion.choices[0].message.content
    logger.debug(f'AI response generated: {response}')
    
    await chat_history.asave_context({"input": transcription}, {"output": response})
    logger.debug('INSIDE THE MEMORY: %s', chat_history.buffer)

    await synthesize_speech(response)
    socketio.emit('new_message', {'message': response, 'sender': 'bot'})  # Emit the AI's response

    if 'i will instruct the technician agent' in response.lower():
        res1 = await asyncio.create_task(initialize_pdf_search_agent(llm, "DO A EXPANSIVE WEB SEARCH AND FAMILIARIZE YOURSELF ALL ABOUT HVAC SPECIFICS SO THAT YOU CAN DIAGNOSE THE PROBLEMS MENTIONED HERE: " + transcription, vectors, chat_history=chat_history))
        
        await chat_history.asave_context({"input": "DO A EXPANSIVE WEB SEARCH AND FAMILIARIZE YOURSELF ALL ABOUT HVAC SPECIFICS SO THAT YOU CAN DIAGNOSE THE PROBLEMS MENTIONED HERE: " + transcription}, {"output": res1})
        
        await synthesize_speech(res1)
        socketio.emit('new_message', {'message': res1, 'sender': 'bot'}) 
    
    if 'questionnaire' in response.lower() and 'complete' in response.lower():
        task = asyncio.create_task(run_quote_logics(client, llm, chat_history=chat_history))
        corrected_quote_result = await task
        response = f"Can you please put this quote into a google doc [{corrected_quote_result}], move it to the folder called 'HVAC Quote Documents'. Then, put all the appointment related stuff and the link to the quote document into calendar (appointment calendar tool). PLEASE FOLLOW THE DIRECTIONS!!"
        task2 = asyncio.create_task(handle_response_with_agents(response))
        text = await task2
        await synthesize_speech(text)
        
    return response

async def handle_response_with_agents(response):
    llm.temperature = 0.5
    logger.debug(f'Processing response with agents: {response}')

    response += "Here is extra info you will need (BUT YOU PROMISE TO NEVER SAY THEM OUT LOUD, NOT EVEN THE NAME -- UNLESS USER ASKS YOU FOR THEM. THESE WILL BE USED IN TOOLS): \nCredentials:\n" + str(credentials)

    # Set the Groq API key randomly
    llm.groq_api_key = random.choice(tools.initialize_groq.api_keys)

    result = agent_executor.invoke({"input": response})
    socketio.emit('finished_chain')
    mystr = (str(result['intermediate_steps']) + "\n" + str(result['output']))

    final_response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "please sanitize this input into SHORT SIMPLE sentences. IMPORTANT: NOTHING IN YOUR RESPONSE SHALL BE ENCLOSED IN ANY QUOTES!!!!!!! THE SANITIZED OUTPUT SHALL NOT BE PREFIXED BY ANYTHING. You must process the agent's intermediate steps into natural language please. An example: 'First, I did this. Then I did this etc etc etc' \n Here is the input that you need to process:\n " + mystr
            }
        ],
        model='llama3-70b-8192',
    ).choices[0].message.content

    await chat_history.asave_context({"input": response}, {"output": final_response})
    return final_response

def synth_speech(text, output_file=None):
    logger.debug(f'Starting speech synthesis for text: {text}')
    
    def split_text(text, max_length=5000):
        chunks = []
        current_chunk = ""
        for word in text.split():
            if len(current_chunk) + len(word) + 1 > max_length:
                chunks.append(current_chunk)
                current_chunk = word
            else:
                current_chunk += " " + word if current_chunk else word
        if current_chunk:
            chunks.append(current_chunk)
        return chunks

    if len(text) <= 5000:
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Casual-K"
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        response = tts_client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        
        with open(os.getenv('TTS_SYNTHESIS'), 'wb') as out:
            out.write(response.audio_content)
        logger.debug('Speech synthesis completed and file saved.')
    else:
        text_chunks = split_text(text)
        combined_audio = b""

        for chunk in text_chunks:
            synthesis_input = texttospeech.SynthesisInput(text=chunk)
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name="en-US-Casual-K"
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            response = tts_client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )
            
            combined_audio += response.audio_content

        with open(os.getenv('TTS_SYNTHESIS'), 'wb') as out:
            out.write(combined_audio)
        logger.debug('Speech synthesis completed and file saved.')
    
    upload_to_gcs(os.getenv('TTS_SYNTHESIS'), BUCKET_NAME, 'synthesis.mp3')
    socketio.emit('tts_complete', {'message': 'TTS synthesis complete', 'file_path': os.getenv('TTS_SYNTHESIS')})
    socketio.emit('new_message', {'message': text, 'sender': 'bot'})  # Emit the synthesized text

async def synthesize_speech(text):
    logger.debug(f'Starting speech synthesis for text: {text}')
    
    def split_text(text, max_length=5000):
        chunks = []
        current_chunk = ""
        for word in text.split():
            if len(current_chunk) + len(word) + 1 > max_length:
                chunks.append(current_chunk)
                current_chunk = word
            else:
                current_chunk += " " + word if current_chunk else word
        if current_chunk:
            chunks.append(current_chunk)
        return chunks

    if len(text) <= 5000:
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Casual-K"
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: tts_client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )
        )
        async with aiofiles.open(os.getenv('TTS_SYNTHESIS'), 'wb') as out:
            await out.write(response.audio_content)
        logger.debug('Speech synthesis completed and file saved.')
    else:
        text_chunks = split_text(text)
        combined_audio = b""

        for chunk in text_chunks:
            synthesis_input = texttospeech.SynthesisInput(text=chunk)
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name="en-US-Casual-K"
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: tts_client.synthesize_speech(
                    input=synthesis_input, voice=voice, audio_config=audio_config
                )
            )
            combined_audio += response.audio_content

        async with aiofiles.open(os.getenv('TTS_SYNTHESIS'), 'wb') as out:
            await out.write(combined_audio)
        logger.debug('Speech synthesis completed and file saved.')
    
    await upload_to_gcs(os.getenv('TTS_SYNTHESIS'), BUCKET_NAME, 'synthesis.mp3')
    socketio.emit('tts_complete', {'message': 'TTS synthesis complete', 'file_path': os.getenv('TTS_SYNTHESIS')})

@app.route('/set_credentials', methods=['POST'])
def set_credentials():
    global credentials
    data = request.get_json()
    if not data:
        return jsonify({"status": "failed", "message": "No data received"}), 400
    credentials['name'] = data.get('name')
    credentials['email'] = data.get('email')
    credentials['recemail'] = data.get('recemail')
    credentials['phone'] = data.get('phone')
    logger.info("THE CREDENTIALS ****** -------------> ", credentials)
    return jsonify({"status": "success"})

@app.route('/')
def index():
    return render_template('index2.html')

@app.route('/voice_assistant')
def voice_assistant():
    return render_template('index2.html')

@app.route('/authenticate', methods=['POST'])
def authenticate():
    auth_header = request.headers.get('Authorization')
    token = auth_header.split(' ')[1] if auth_header else None

    if not token:
        return jsonify({'error': 'Missing token'}), 400

    response = requests.get(
        'https://www.googleapis.com/oauth2/v3/userinfo',
        headers={'Authorization': f'Bearer ' + token}
    )

    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch user info'}, response.status_code)

    user_info = response.json()
    return jsonify(user_info), 200

@app.route('/talk', methods=['POST'])
async def talk():
    data = request.get_json()
    audio_url = data.get('RecordingUrl')

    if not audio_url:
        return jsonify({"error": "No audio URL provided"}), 400
    
    logger.debug('Starting audio transcription...')
    transcription = await transcribe_audio(audio_url)
    logger.debug(f'Audio transcription completed: {transcription}')
    
    logger.debug('Generating AI response...')
    ai_resp = await ai_response(transcription)
    logger.debug(f'AI response generated: {ai_resp}')
    
    return jsonify({'response': ai_resp})

@app.route('/text_input', methods=['POST'])
async def text_input():
    data = request.get_json()
    text = data.get('text', '')

    if not text:
        return jsonify({"error": "No text provided"}), 400

    logger.debug('Generating AI response...')
    ai_resp = await ai_response(text)
    logger.debug(f'AI response generated: {ai_resp}')
    
    return jsonify({'response': ai_resp})

@app.route('/synthesize', methods=['POST'])
async def synthesize():
    data = request.get_json()
    text = data.get('text', '')
    await synthesize_speech(text)
    return jsonify({"status": "synthesis started"}), 200

@app.route('/get_audio')
def get_audio():
    return send_file(tts_synthesis_path, mimetype="audio/mp3")

import queue

human_response_queue = queue.Queue()

def web_prompt_func(prompt):
    text = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "please sanitize this input into SHORT SIMPLE sentences. IMPORTANT: NOTHING IN YOUR RESPONSE SHALL BE ENCLOSED IN ANY QUOTES!!!!!!! KEEP ID'S AS THEY ARE!!! THE SANITIZED OUTPUT SHALL NOT BE PREFIXED BY ANYTHING. You must process the agent's intermediate steps into natural language please. An example: 'First, I did this. Then I did this etc etc etc' \n Here is the input that you need to process:\n " + prompt
            }
        ],
        model='llama3-70b-8192',
    ).choices[0].message.content
    synth_speech(text, output_file=tts_synthesis_path)
    return prompt

def web_input_func():
    socketio.emit('request_human_input')
    human_response = human_response_queue.get()  # Block until human input is available
    return human_response

@socketio.on('provide_human_input')
def handle_human_input(data):
    human_input = data.get('text', '')
    human_response_queue.put(human_input)  # Put the human's response in the queue
    socketio.emit('human_input_received', {'status': 'received'})

from langchain_community.tools import HumanInputRun

human_tool = HumanInputRun(prompt_func=web_prompt_func, input_func=web_input_func)
my_tools.append(human_tool)

search_agent = create_structured_chat_agent(llm, my_tools, prompt)
agent_executor = AgentExecutor(
    agent=search_agent,
    tools=my_tools,
    verbose=True,
    handle_parsing_errors=True,
    return_intermediate_steps=True,
    memory=chat_history
)

@app.route('/voice', methods=['GET', 'POST'])
def voice():
    response = VoiceResponse()
    tts_synthesis_url = os.getenv('TTS_SYNTHESIS_URL', f'https://storage.googleapis.com/tts-synthesis-bucket/synthesis.mp3')

    if not tts_synthesis_url:
        response.say("We have encountered technical difficulties.", voice='alice')
    else:
        response.play(tts_synthesis_url)
        gather = Gather(input='speech', action='/talk', method='POST')
        response.append(gather)

    return str(response)

@app.route('/fetch-call-logs', methods=['GET'])
def fetch_call_logs():
    try:
        logger.debug("Attempting to fetch call logs from Twilio")
        calls = twilio_client.calls.list()
        call_data = [{
            'sid': call.sid,
            'from': call._from,
            'to': call.to,
            'start_time': call.start_time.isoformat() if call.start_time else None,
            'date_created': call.date_created.isoformat() if call.date_created else None,
            'date_updated': call.date_updated.isoformat() if call.date_updated else None,
            'status': call.status,
            'direction': call.direction,
            'duration': call.duration,
            'price': call.price,
            'price_unit': call.price_unit,
            'recordings': [{'sid': recording.sid, 'uri': recording.uri} for recording in call.recordings.list()]
        } for call in calls]
        logger.debug(f"Fetched {len(call_data)} call logs from Twilio")
        return jsonify(call_data)
    except Exception as e:
        logger.error(f'Error fetching call logs: {e}', exc_info=True)
        return jsonify({'error': 'Error fetching call logs'}), 500

@app.route('/fetch-recording', methods=['GET'])
def fetch_recording():
    recording_url = request.args.get('url')
    try:
        response = requests.get(recording_url, auth=(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN')), stream=True)
        response.raise_for_status()
        return send_file(BytesIO(response.content), mimetype='audio/mpeg')
    except Exception as e:
        logger.error(f'Error fetching recording: {e}', exc_info=True)
        return jsonify({'error': 'Error fetching recording'}), 500

if __name__ == '__main__':
    socketio.run(app, allow_unsafe_werkzeug=True)
