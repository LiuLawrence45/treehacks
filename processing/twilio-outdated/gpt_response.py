
from openai import OpenAI
import os
import dotenv
dotenv.load_dotenv()



def generate_gpt_response(input_text):


    client = OpenAI(
        # This is the default and can be omitted
        api_key=os.getenv("OPENAI_KEY")
    )

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


def generate_user_response(input_audio):
        
    client = OpenAI()

    audio_file = open("speech.mp3", "rb")
    transcript = client.audio.transcriptions.create(
    model="whisper-1", 
    file=audio_file, 
    response_format="text"
    )