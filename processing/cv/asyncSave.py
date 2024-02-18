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
from createCache import process_frames_with_gpt4, FrameCache, analyze_and_summarize, analyze_cache
import sys
from threading import Thread
import uuid
# Load the model
# model = YOLO('processing/cv/smallest-YOLO.pt')



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

user_flag = input("Enter the objects or actions you want to flag: ")

client = ImageAnalysisClient(endpoint = endpoint, credential = AzureKeyCredential(subscription_key))
cap = cv2.VideoCapture(0)


#Initialize FrameCache for GPT 4 
frame_cache = FrameCache(reset_interval=10)

executor = ThreadPoolExecutor(max_workers=6)

language = "en"
max_descriptions = 3

frame_counter = 0

# Define a comprehensive list of visual features available
visual_features =[
        VisualFeatures.DENSE_CAPTIONS,
        VisualFeatures.PEOPLE,
    ]

def process_frame(frame, results_array):
    try:
        _, buffer = cv2.imencode('.jpg', frame)
        stream = BytesIO(buffer)

        #azure inference
        result = client.analyze(
        image_data=stream,
        visual_features=visual_features,
        language="en"
        )

        results_array.append(result)

        print(" Dense Captions:")
        for caption in result.dense_captions.list:
            print(f"   '{caption.text}', {caption.bounding_box}, Confidence: {caption.confidence:.4f}")

        print(" People:")
        for person in result.people.list:
            print(f"   {person.bounding_box}, Confidence {person.confidence:.4f}")

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

        frame_cache.add_frame(frame)

        # Process every 24th frame to reduce load
        if i % 24 == 0:
            executor.submit(process_frame, frame, results_array)

        if i % (30*4) == 0:
            batch_id = i
            cached_frames = frame_cache.get_and_clear()
            executor.submit(process_frames_with_gpt4, cached_frames, results_array, batch_id)
            analyze_thread = Thread(target=analyze_cache, args=(results_array, batch_id, user_flag))
            analyze_thread.start()
            results_array = []
        cv2.imshow('Video', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
   # future.result() # WAITING FOR FUTURE TO FINISH
    cap.release()
    cv2.destroyAllWindows()
