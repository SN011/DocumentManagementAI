
from google.cloud import texttospeech
from google.oauth2 import service_account
credentials = service_account.Credentials.from_service_account_file("D:\\DEV\\WebdevFolder\\realestateai-doc-mgr-051849e19181.json")


client = texttospeech.TextToSpeechClient(credentials=credentials)

text_input = texttospeech.SynthesisInput(text="Hello, world!")


voice = texttospeech.VoiceSelectionParams(
    language_code="en-US",
    name="en-US-Casual-K"
)


audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.MP3
)


response = client.synthesize_speech(
    input=text_input, voice=voice, audio_config=audio_config
)


with open("googleTTSoutput.mp3", "wb") as out:
    out.write(response.audio_content)
    print('Audio content written to file "googleTTSoutput.mp3"')



