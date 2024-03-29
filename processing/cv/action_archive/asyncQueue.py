from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes, VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
from array import array
import os
from PIL import Image
import sys
import time
import cv2
from io import BytesIO
import dotenv
from concurrent.futures import ThreadPoolExecutor
dotenv.load_dotenv()
import json
import requests
from ultralytics import YOLO  # Assuming YOLOv8 is accessible through ultralytics
from createCache import process_frames_with_gpt4, FrameCache
import sys
from queue import Queue
from threading import Thread
# Load the model
model = YOLO('processing/cv/smallest-YOLO.pt')


frame_queue = Queue()

def frame_processor():
    while True:
        item = frame_queue.get()
        if item is None:  # Stop signal
            break
        if item == ('bulk_process', None):  # Special signal for bulk processing
            cached_frames = frame_cache.get_and_clear()
            executor.submit(process_frames_with_gpt4, cached_frames, results_array)
            continue

        index, frame = item  # Unpack the tuple
        if index % 12 == 0:  # Process every 12th frame
            # Add frame to cache or directly process it
            frame_cache.add_frame(frame)
            if frame_cache.should_process():  # Implement this method based on your logic
                cached_frames = frame_cache.get_and_clear()
                executor.submit(process_frames_with_gpt4, cached_frames, results_array)

# Start a few worker threads
for _ in range(5):  # Adjust the number of threads based on your needs
    Thread(target=frame_processor, daemon=True).start()

analysis_results = []
# General variables
subscription_key = os.getenv("AZURE_API_KEY")
endpoint = os.getenv("VISION_ENDPOINT")

analyze_url = f"{endpoint}vision/v4.0/analyze"

headers = {
    'Ocp-Apim-Subscription-Key': subscription_key,
    'Content-Type': 'application/octet-stream'
}


params = {
    'visualFeatures': 'DenseCaption',
    'model-version': 'latest'
}

    

client = ImageAnalysisClient(endpoint = endpoint, credential = AzureKeyCredential(subscription_key))
cap = cv2.VideoCapture(0)


#Initialize FrameCache for GPT 4 
frame_cache = FrameCache(reset_interval=6)

executor = ThreadPoolExecutor(max_workers=4)

language = "en"
max_descriptions = 3

frame_counter = 0

# Define a comprehensive list of visual features available
visual_features =[
        VisualFeatures.TAGS,
        VisualFeatures.OBJECTS,
        VisualFeatures.CAPTION,
        VisualFeatures.DENSE_CAPTIONS,
        VisualFeatures.READ,
        VisualFeatures.SMART_CROPS,
        VisualFeatures.PEOPLE,
    ]


# def run_yolov8(frame):
#     results = model(frame)
#     # Process results as needed, e.g., extract bounding boxes, labels, etc.
#     return results.to_dict()  # Assuming results can be converted to a dictionary

def process_frame(frame, results_array):
    try:
        _, buffer = cv2.imencode('.jpg', frame)
        stream = BytesIO(buffer)

        # yolov8 inference
        # yolov8_results = run_yolov8(frame)

        #azure inference
        result = client.analyze(
        image_data=stream,
        visual_features=visual_features,
        language="en"
        )

        results_array.append(result)

        print(" Caption:")
        print(f"   '{result.caption.text}', Confidence {result.caption.confidence:.4f}")

        print(" Dense Captions:")
        for caption in result.dense_captions.list:
            print(f"   '{caption.text}', {caption.bounding_box}, Confidence: {caption.confidence:.4f}")

        print(" Read:")
        for line in result.read.blocks[0].lines:
            print(f"   Line: '{line.text}', Bounding box {line.bounding_polygon}")
            for word in line.words:
                print(f"     Word: '{word.text}', Bounding polygon {word.bounding_polygon}, Confidence {word.confidence:.4f}")

        print(" Tags:")
        for tag in result.tags.list:
            print(f"   '{tag.name}', Confidence {tag.confidence:.4f}")

        print(" Objects:")
        for object in result.objects.list:
            print(f"   '{object.tags[0].name}', {object.bounding_box}, Confidence: {object.tags[0].confidence:.4f}")

        print(" People:")
        for person in result.people.list:
            print(f"   {person.bounding_box}, Confidence {person.confidence:.4f}")

        print(" Smart Cropping:")
        for smart_crop in result.smart_crops.list:
            print(f"   Aspect ratio {smart_crop.aspect_ratio}: Smart crop {smart_crop.bounding_box}")

    except Exception as e:
        print(f"Exception in processing frame: {e}")

try:
    i = 0
    results_array = []
    while True:
        ret, frame = cap.read()
        i += 1
        if not ret:
            print("Failed to grab frame")
            break

        #frame_cache.add_frame(frame)
        frame_queue.put((i, frame))

        # Process every 12th frame to reduce load
        # if i % 12 == 0:
        #     executor.submit(process_frame, frame, results_array)

        if i % (30*6) == 0:
            frame_queue.put(('bulk_process', None))
        cv2.imshow('Video', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    for _ in range(5):  # Same number as the worker threads you started
        frame_queue.put(None)
    cap.release()
    cv2.destroyAllWindows()