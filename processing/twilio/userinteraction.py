from flask import Flask, request, jsonify
from twilio.twiml.voice_response import VoiceResponse
from openai import OpenAI
import os
from twilio.rest import Client
import dotenv

dotenv.load_dotenv()

app = Flask(__name__)

# Load your environment variables
twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")

twilio_client = Client(twilio_account_sid, twilio_auth_token)

@app.route("/", methods=['GET', 'POST'])
def answer_call():
    """Responds to incoming calls with a simple text-to-speech message."""
    resp = VoiceResponse()
    
    # Use <Gather> to capture speech input, assuming callback to '/process_speech'
    gather = resp.gather(input='speech', action='/process_speech', method='POST')
    gather.say("Hello, please tell me something and I will respond.")
    
    return str(resp)

@app.route("/process_speech", methods=['POST'])
def process_speech():
    """Processes speech input from the caller, sends it to Whisper, and responds."""
    # Fetch the speech transcription result
    speech_text = request.values.get("SpeechResult", None)
    
    # Generate a response using OpenAI's GPT
    if speech_text:
        response_text = generate_gpt_response(speech_text)
    else:
        response_text = "I'm sorry, I didn't catch that. Could you repeat please?"

    # Create a TwiML response to read the GPT-generated message back to the caller
    resp = VoiceResponse()
    resp.say(response_text)
    return str(resp)



client = OpenAI(
    # This is the default and can be omitted
    api_key=os.getenv("OPENAI_KEY")
)


def generate_gpt_response(input_text):
    """Generates a text response using OpenAI's GPT based on the input text."""
    try:
        # Adjust the function call according to the latest version of the library
        gpt_response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Say this is a test",
                }
            ],
            model="gpt-3.5-turbo",
        )
        response_text = gpt_response.choices[0].message.content
    except Exception as e:
        response_text = "Sorry, I couldn't generate a response due to an error."
        print(f"Error generating GPT response: {e}")
    
    return response_text

if __name__ == "__main__":
    app.run(debug=True)
