from flask import Flask
from twilio.twiml.voice_response import VoiceResponse, Start

app = Flask(__name__)



@app.route("/", methods=['GET', 'POST'])
def answer_call():
    """Respond to incoming phone calls with a brief message."""
    # Start our TwiML response
    resp = VoiceResponse()
    start = Start()
    start.stream(
        name = "Example Audio Stream", url='wss://mystream.ngrok.io/audiostream'
    )

    # Read a message aloud to the caller
    resp.say("Thank you for calling! Have a great day.", voice='Polly.Amy')

    return str(resp)

@app.route("/audiostream", methods=['GET', 'POST'])
def audio_stream():
    return "Hello, World!"

if __name__ == "__main__":
    app.run(debug=True)