from threading import Lock
from time import sleep
import threading
import cv2
import numpy as np
import os
import uuid

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