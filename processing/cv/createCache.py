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




def process_frames_with_gpt4(frames, results):
    print(f"Processing {len(frames)} frames with GPT-4")



    # Generate unique id. 
    batch_id = uuid.uuid4()

    dynamic_name, summary = analyze_and_summarize(results, batch_id)

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



def analyze_and_summarize(results):
    # Assuming results is a list of dictionaries or similar structure that GPT can process
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
                {"role": "system", "content": "You are a highly intelligent AI trained to summarize results."},
                {"role": "user", "content": f"Summarize these results: {results_json}"}
            ],
            temperature=0.5,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )

        # Extracting text from the response
        summary = response.choices[0].message.content.strip()

        # For dynamic naming, you could use a part of the summary or any other logic
        dynamic_name = "Summary_" + str(uuid.uuid4())
        print("Dynamic name: ", dynamic_name)
        print("Summary:" , summary)
        return dynamic_name, summary
    
    except Exception as e:
        print(f"Error in analyze_and_summarize: {e}")
        return "Error", "Could not analyze and summarize results."
    

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
