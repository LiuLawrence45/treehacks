from threading import Lock
from time import sleep
import threading
import cv2
import numpy as np
import os
import uuid
from dotenv import load_dotenv
import json
from openai import OpenAI
import subprocess
import threading
import requests
from shared_resources import execution_lock, has_executed

load_dotenv()
process_lock = threading.Lock()

class FrameCache:
    def __init__(self, reset_interval=6):
        self.frames = []
        self.lock = Lock() #only one thread can run
        self.reset_interval = reset_interval
        self.reset_thread = threading.Thread(target=self.reset_cache, daemon=True) # daemon, won't continue if its the only thread running. 
        self.reset_thread.start()

    def add_frame(self, frame):
        with self.lock:
            self.frames.append(frame)

    def get_and_clear(self):
        with self.lock:
            frames_copy = self.frames.copy()
            self.frames.clear()
            return frames_copy
    
    def reset_cache(self):
        while True:
            sleep(self.reset_interval)
            with self.lock:
                self.frames.clear()

has_called = False

def process_frames_with_gpt4(frames, results, batch_id):
    # print(f"Processing {len(frames)} frames with GPT-4")



    # Generate unique id. 
    # batch_id = uuid.uuid4()

    # dynamic_name, summary = analyze_and_summarize(results, batch_id)


    # Get the frame width and height
    if frames:
        height, width = frames[0].shape[:2]
    else:
        width = height = 0
    # Use XVID codec for saving as AVI which is widely supported.
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_filename = f'processing/cv/cache/{batch_id}.mp4'
    out = cv2.VideoWriter(video_filename, fourcc, 20.0, (width, height))
    
    for frame in frames:
        out.write(frame)
    out.release()

    results_filename = f'processing/cv/cache/{batch_id}.txt'
    with open(results_filename, 'w') as file:
        for result in results:
            file.write(str(result) + '\n')

    print(f"Saved frames to {video_filename} and results to {results_filename}.")




def analyze_and_summarize(results, batch_id, user_flag): ## HELPER
    # Assuming results is a list of dictionaries or similar structure that GPT can process
    global has_executed
    try:
        client = OpenAI(
                # This is the default and can be omitted
                api_key=os.environ.get("OPENAI_API_KEY"),
            )

        # Convert results to JSON string for GPT processing
        results_json = json.dumps(results)
        
        # Call the OpenAI API with the results using GPT-4
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"""          
You are a company secretary that only speaks in JSON. Do not generate output that is not in properly formatted JSON. The input has the following format, composed of a list of chronological model outputs that contain the following.
                 
                 1. 'denseCaptionsResult': describing the bounding box location of specific object in an image frame, along with text describing the object
                 2. 'peopleResult': describing the bounding box location of people in a given frame.
        
Remember, the model outputs are chronological. Those at the top of the input happened earlier than those later in the input. 

Analyze the entire frame deeply to see if user query {user_flag} has relevance. Relevance will be assigned a boolean value in variable `relevance`. Here are examples of relevance.

Example 1: User Flag = "cat"
    Input Data:

    Frame 1:
    denseCaptionsResult: A small cat sitting on a windowsill, looking outside.
    peopleResult: No people detected in this frame.
    Frame 2:
    denseCaptionsResult: The same cat now lying down, still on the windowsill.
    peopleResult:"No people detected in this frame.
    Analysis:

    The user query is specifically looking for a "cat".
    The denseCaptionsResult for both frames explicitly mentions a cat in the scene.
    There are no interactions with people as peopleResult indicates no human presence.
    Output:
        {{
        "relevance": true,
        "reason": "The video contains multiple frames showing a cat, directly matching the user's query."
        }}
Example 2: User Flag = "group of people dancing"
    Frame 1:
    denseCaptionsResult: A group of five people dancing in a circle.
    peopleResult: Bounding boxes showing five people closely interacting.
    Frame 2:
    denseCaptionsResult: The group continues to dance, one person is jumping.
    peopleResult: "Bounding boxes still show five people, with one depicted in a jumping pose."
    Analysis:

    The user query is about "group of people dancing".
    Both the denseCaptionsResult and peopleResult confirm the presence and activity of a group dancing over multiple frames.
    Output:
        {{
        "relevance": true,
        "reason": "The frames consistently show a group of people dancing, which aligns with the user's query."
        }}
Example 3: User Flag = "sunset"
    Input Data:

    Frame 1:
    denseCaptionsResult: A beautiful sunset visible behind mountains.
    peopleResult: No people detected in this frame.
    Frame 2:
    denseCaptionsResult: The sun has almost set, with vibrant colors in the sky.
    peopleResult: A silhouette of a person admiring the sunset.
    Analysis:

    The user query is looking for a "sunset".
    The denseCaptionsResult for both frames captures the essence of a sunset, making it relevant.
    The presence of a person in the second frame does not detract from the relevance to the sunset query.
    Output:
        {{
        "relevance": true,
        "reason": "Both frames feature the sunset, which is the main focus of the user's query."
        }}
Example 4: User Flag = "fast-moving car"
    Input Data:

    Frame 1:
    denseCaptionsResult: A car speeding on a highway, motion blur visible.
    peopleResult: No people detected outside of the car.
    Frame 2:
    denseCaptionsResult: The car continues to speed, now changing lanes.
    peopleResult: No people detected outside of the car.
    Analysis:

    The user query is about a "fast-moving car".
    The denseCaptionsResult in both frames clearly indicates the presence of a car moving at high speed, with details like motion blur and lane changing supporting this.
    Output:
        {{
        "relevance": true,
        "reason": "The video consistently shows a fast-moving car across multiple frames, aligning with the user's query."
        }}
The output must abide by the following rules.
 1. ALWAYS FINISH THE OUTPUT. Never send partial responses
 2. The output should ALWAYS be formatted as a JSON as such:
        {{
            "relevance": true,
            "reason": "reasoning for relevance"
        }}

Take a deep breath, and think.
"""
},
                {"role": "user", "content": f"{results_json}"}
            ],
            temperature=0.5,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )

        # Extracting text from the response
        summary = response.choices[0].message.content.strip()

        try:
            gpt_response_json = json.loads(summary)
            
            # Check if 'relevance' is true in the response
            if gpt_response_json.get('relevance') is True:
                with execution_lock:
                    if not has_executed:
                        # If relevant, execute the command
                        print("Relevance is true, executing command...")
                        final_response = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": f"""          
                        You are a prompt generator. Look at the following examples. Make sure that your output always abides with JSON syntax and formatting. MAKE SURE TO ALWAYS FORMAT AS A JSON, with correct syntax. Never leave an output unfinished. 
                        1. Input: elderly person falling
                            Output: {{
                                        "systemPrompt": "You are a calm and reassuring communicator, tasked with calling an emergency contact for an elderly person who has experienced a fall. Make sure to simply just explain that an elderly person has fell, no need for names. Your voice embodies compassion and patience, ensuring that your message conveys urgency without instilling panic. Your primary aim is to collect essential information while also offering solace to the emergency contact. Structure your queries to be clear and direct, limiting yourself to one question at a time to prevent overwhelming the listener. Inquire about the elderly individual's medical history and any immediate necessities, asking questions such as 'Do you know if they have any medical conditions I should be informed of?'. If the user asks for an ambulance, do not ask them any further questions and call the makeEmergencyCall function. Furthermore, in scenarios where the situation appears critical but there is no request for an ambulance, propose the option of summoning an ambulance in a gentle manner, asking, 'Would it be advisable for me to call an ambulance at this moment?'. Conversely, if the contact believes everything is under control, accept their assessment without insisting on further inquiries. Throughout the conversation, ensure to express your support and reassurance, reminding the contact of your readiness to assist. Incorporate a '•' symbol every 5 to 10 words, at natural pauses, to facilitate a fluid transition for text to speech delivery.",
                                        "assistantPrompt": "Hey there! Did you fall?"
                                    }}
                                
                        2. Input: Child lost in a mall
                                Output: {{
                                "systemPrompt": "You are a composed and empathetic communicator, tasked with informing a parent that their child has been found wandering alone in a mall. Your tone is comforting and patient, ensuring your message alleviates worry without causing distress. Your main goal is to collect important information while providing reassurance to the parent. Structure your questions to be clear and concise, asking one thing at a time to keep the conversation calm. Inquire about the child's name and any distinctive features or clothing to help identify them, such as 'Can you describe what they're wearing today?'. If the parent starts to panic, remind them calmly that the child is safe and ask if there's a preferred meeting point in the mall. Conversely, if the parent is nearby and can come immediately, confirm their arrival time, asking, 'How quickly can you get here?'. Throughout the exchange, emphasize your support and readiness to help, using pauses marked by '•' every 5 to 10 words to ensure clarity for text-to-speech delivery.",
                                "assistantPrompt": "Hey there! You look lost. Is everything okay?"
                                }}
                                
                        3. Input: water bottle falling
                            Output: {{
                            "systemPrompt": "You are a keen and observant communicator, tasked with addressing the moment a water bottle falls over in a quiet environment. Your tone is composed and attentive, ensuring your message captures the slight but noticeable event without causing any alarm. Your main goal is to calmly acknowledge the incident while offering to assist in any small way necessary. Ask a straightforward question, focusing on the immediate need, such as 'Would you like me to pick up the water bottle for you?'. If the situation seems to bother someone, offer a gentle reassurance, 'It's just a small spill, shall we clean it up together?'. Throughout the interaction, emphasize your willingness to help, inserting '•' every 5 to 10 words to facilitate clear and calm communication.",
                            "assistantPrompt": "Hey there! Looks like your water bottle fell"
                            }}
                                
                        4. Input: person jumping
                            Output: {{
                            "systemPrompt": "You are an energetic and encouraging communicator, tasked with cheering on someone who is jumping, perhaps as part of an exercise or a joyful expression. Your voice is full of enthusiasm and support, making sure your message boosts their spirits without overwhelming them. Your primary aim is to motivate and acknowledge their effort, asking in a spirited manner, 'How high can you go? Keep it up!'. If they seem to be enjoying themselves, join in their excitement, 'That looks fun! Mind if I join you?'. Throughout the exchange, ensure to express your positive energy, using '•' every 5 to 10 words to keep the encouragement lively and engaging.",
                            "assistantPrompt": "Hey! Looking good, need any tips or just cheering on while you're jumping?"
                            }}
                        5. Input: person falling
                                Output: {{
                                "systemPrompt": "You are a compassionate and alert communicator, tasked with responding to someone who has just fallen. Your tone is caring and calm, ensuring your message offers support without adding to any embarrassment or discomfort. Your main goal is to assess their well-being and offer assistance, asking gently, 'Are you alright? Can I help you up?'. If they appear to be hurt, suggest further action in a reassuring manner, 'Do you need any medical attention or someone to call for help?'. Throughout the interaction, your focus is on their safety and comfort, inserting '•' every 5 to 10 words to ensure your concern is clearly communicated without rushing.",
                                "assistantPrompt": "Oh no! Are you okay? Do you need help getting up?"
                                }}
                                
                        6. Input: Water bottle
                            Output: {{
                            "systemPrompt": "You are a thoughtful and environmentally conscious communicator, tasked with discussing the importance of staying hydrated and the benefits of using a reusable water bottle. Your tone is informative and encouraging, aiming to inspire positive habits without sounding judgmental. Begin by acknowledging the value of hydration, 'Staying hydrated is key to maintaining good health. Do you carry a water bottle with you?'. If the response is positive, commend their habit and perhaps suggest ways to make hydration more enjoyable, like adding fruit for flavor. If they don't have one, gently suggest the benefits of a reusable water bottle for both health and environmental reasons, 'A reusable water bottle can be a great companion throughout the day, and it's good for the planet too! Would you like some recommendations?'. Throughout the conversation, use '•' every 5 to 10 words to ensure your advice is clear and engaging.",
                            "assistantPrompt": "Hello! How can I assist you in staying hydrated today?"
                            }}
                        
                        7. Input: Ritz crackers
                            Output: {{
                            "systemPrompt": "You are a creative and culinary-minded communicator, tasked with sharing some fun and tasty snack ideas using Ritz crackers. Your tone is enthusiastic and inviting, aiming to spark culinary creativity and a love for simple, delicious snacks. Begin by highlighting the versatility of Ritz crackers, 'Ritz crackers are not just tasty on their own, but also a fantastic base for a variety of snacks. Have you tried any creative toppings?'. If they're looking for suggestions, offer a few easy yet delightful combinations, like cheese and apple slices or peanut butter and banana. Encourage them to experiment with their own ideas, 'What’s your favorite topping? There's so much you can do with them!'. Throughout the exchange, use '•' every 5 to 10 words to keep the suggestions clear and the conversation flowing smoothly.",
                            "assistantPrompt": "Hey there! Ready to whip up some tasty snacks with Ritz crackers?"
                            }}

                        """
                        },
                                        {"role": "user", "content": f"{user_flag}"}
                                    ],
                                    temperature=0.5,
                                    top_p=1.0,
                                    frequency_penalty=0.0,
                                    presence_penalty=0.0
                                )
                        summary = final_response.choices[0].message.content.strip()

                        # try: 
                        payload = json.loads(summary)

                        data_to_send = {
                            "systemPrompt" : payload.get('systemPrompt'),
                            "assistantPrompt" : payload.get('assistantPrompt')
                        }
                        response = requests.post("http://127.0.0.1:5000/data", json=data_to_send)
                        print("Response is: ", response.text)
                        # except:
                        #     data_to_send = {
                        #         "systemPrompt" : """ You are a calm and reassuring communicator. Your voice embodies compassion and patience, ensuring that your message conveys urgency without instilling panic. Your primary aim is to collect essential information about the caller, asking about their day. Structure your queries to be clear and direct, limiting yourself to one question at a time to prevent overwhelming the listener. Incorporate a '•' symbol every 5 to 10 words, at natural pauses, to facilitate a fluid transition for text to speech delivery.""",
                        #         "assistantPrompt" : "Hey! How is your day going?"
                        #     }
                        response = requests.post("http://127.0.0.1:5000/data", json=data_to_send)
                        


                        # has_called = True
                        
                        subprocess.run(["npm", "run", "outbound"], cwd="/Users/lawrenceliu/23-24 Projects/treehacks/call-gpt/scripts")

            else:
                print("Relevance is false, not executing command.")
        except json.JSONDecodeError:
            print("Failed to parse GPT response as JSON.")

        # For dynamic naming, you could use a part of the summary or any other logic
        # dynamic_name = "Summary_" + str(uuid.uuid4())
        dynamic_name = "Summary_" + str(batch_id)
        print("Dynamic name: ", dynamic_name)
        print("Summary:" , summary)
        return dynamic_name, summary
    
    except Exception as e:
        print(f"Error in analyze_and_summarize: {e}")
        return "Error", "Could not analyze and summarize results."
    

def analyze_cache_all():
    cache_folder = 'processing/cv/cache/'
    for filename in os.listdir(cache_folder):
        if filename.endswith('.txt'):
            with open(os.path.join(cache_folder, filename), 'r') as file:
                results = [line.strip() for line in file.readlines()]
                dynamic_name, summary = analyze_and_summarize(results)
                summary_json = json.dumps({'name': dynamic_name, 'summary': summary})
                # print(f"Processed {filename}: {summary_json}")
                # Write the filename and summary to another file in the cache folder
                summary_filename = os.path.join(cache_folder, f"{dynamic_name}_summary.txt")
                with open(summary_filename, 'w') as summary_file:
                    summary_file.write(f"Filename: {filename}\nSummary: {summary}")
                # print(f"Saved summary to {summary_filename}")

def analyze_cache(results_array, batch_id, user_flag):
    cache_folder = 'processing/cv/cache/'
    
    # Convert ImageAnalysisResult objects in results_array to a serializable format
    results_array_serializable = [result.as_dict() for result in results_array]
    dynamic_name, summary = analyze_and_summarize(results_array_serializable, batch_id, user_flag)
    summary_json = json.dumps({'name': dynamic_name, 'summary': summary})
    # Write the filename and summary to another file in the cache folder
    summary_filename = os.path.join(cache_folder, f"{dynamic_name}.txt")
    with open(summary_filename, 'w') as summary_file:
        summary_file.write(f"Filename: {dynamic_name}\nSummary: {summary}")
    print(f"Saved summary to {summary_filename}")


    

if __name__ == "__main__":

    cache_folder = 'processing/cv/cache/'
    for filename in os.listdir(cache_folder):
        if filename.endswith('.txt'):
            with open(os.path.join(cache_folder, filename), 'r') as file:
                results = [line.strip() for line in file.readlines()]
                dynamic_name, summary = analyze_and_summarize(results)
                summary_json = json.dumps({'name': dynamic_name, 'summary': summary})
                print(f"Processed {filename}: {summary_json}")
                # Write the filename and summary to another file in the cache folder
                summary_filename = os.path.join(cache_folder, f"{dynamic_name}_summary.txt")
                with open(summary_filename, 'w') as summary_file:
                    summary_file.write(f"Filename: {filename}\nSummary: {summary}")
                print(f"Saved summary to {summary_filename}")
