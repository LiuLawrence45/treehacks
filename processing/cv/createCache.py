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

load_dotenv()

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




def process_frames_with_gpt4(frames, results, batch_id):
    print(f"Processing {len(frames)} frames with GPT-4")



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
    # global has_run_subprocess
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
                 
### OLD PROMPT.       
# You are a company secretary that only speaks in JSON. Do not generate output that is not in properly formatted JSON. The input has the following format, composed of a list of chronological model outputs that contain the following.
#                  1. 'denseCaptionsResult': describing the bounding box location of specific object in an image frame, along with text describing the object
#                  2. 'peopleResult': describing the bounding box location of people in a given frame.
        
# Remember, the model outputs are chronological. Those at the top of the input happened earlier than those later in the input. 

# Most importantly, extract and infer information from the input, specifically of people movements, interactions, and objects of prominence in the given frame. The output must abide by the following rules.
#                  1. ALWAYS FINISH THE OUTPUT. Never send partial responses
#                  2. When inferencing people movement, generate it as variable `summarized_actions`. This variable should show prominent actions and interactions that are inferred from movements of objects and people in frame. Be creative, yet accurate with finding interactions between objects/people. There should be logical jumps made from the data given--take a deep breath and think about what people movements are implied from the input. Further, the variable `summarized_objects`, should be a list of objects that are in frame and are prominent. `summarized objects` should look like, ["water bottle", "chips", "phone."]. 
                 
#                  3. The output should ALWAYS be formatted as a JSON as such:
#                     {
#                         "action": [{"summary": `summarized_actions`}],
#                         "objects":[{"object": `summarized_objects`}]
#                     }
# """
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
                # If relevant, execute the command
                print("Relevance is true, executing command...")
                # has_run_subprocess = True
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
