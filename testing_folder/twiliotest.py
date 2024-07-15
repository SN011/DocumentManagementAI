# %%
import os
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

# Localtunnel URL (replace with your actual Localtunnel URL)
LOCALTUNNEL_URL = os.getenv('LOCALTUNNEL_URL')

# Initialize the Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

app = Flask(__name__)

@app.route('/make_call', methods=['POST'])
def make_call():
    data = request.get_json()
    to_phone_number = data.get('to_phone_number')
    message = data.get('message')

    if not to_phone_number or not message:
        return jsonify({"error": "Missing 'to_phone_number' or 'message'"}), 400
    
    if not to_phone_number.startswith('+1') or len(to_phone_number) != 12:
        return jsonify({"error": "Invalid US phone number. It should be in the format +1XXXXXXXXXX"}), 400

    call = client.calls.create(
        to=to_phone_number,
        from_=TWILIO_PHONE_NUMBER,
        url='http://35.245.222.90/voice'
    )
    return jsonify({"status": "call initiated", "sid": call.sid})

@app.route('/send_sms', methods=['POST'])
def send_sms():
    data = request.get_json()
    to_phone_number = data.get('to_phone_number')
    message = data.get('message')

    if not to_phone_number or not message:
        return jsonify({"error": "Missing 'to_phone_number' or 'message'"}), 400
    
    if not to_phone_number.startswith('+1') or len(to_phone_number) != 12:
        return jsonify({"error": "Invalid US phone number. It should be in the format +1XXXXXXXXXX"}), 400

    message = client.messages.create(
        body=message,
        from_=TWILIO_PHONE_NUMBER,
        to=to_phone_number
    )
    return jsonify({"status": "SMS sent", "sid": message.sid})

@app.route('/voice', methods=['GET','POST'])
def voice():
    response = VoiceResponse()
    response.play(os.getenv('TTS_SYNTHESIS'))
    return str(response)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)


