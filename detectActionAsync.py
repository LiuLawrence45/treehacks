from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes, VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials
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

# General variables
subscription_key = os.getenv("AZURE_API_KEY")
endpoint = os.getenv("VISION_ENDPOINT")
computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))
cap = cv2.VideoCapture(1)

executor = ThreadPoolExecutor(max_workers=2)

language = "en"
max_descriptions = 3

frame_counter = 0

def process_frame(frame):
    try:
        _, buffer = cv2.imencode('.jpg', frame)
        stream = BytesIO(buffer)

        # Detect objects in the frame
        detected_objects_future = executor.submit(computervision_client.detect_objects_in_stream, stream)

        stream.seek(0)

        description_future = executor.submit(computervision_client.describe_image_in_stream, stream, max_descriptions, language)

        detected_objects = detected_objects_future.result()
        analysis = description_future.result()

        for caption in analysis.captions:
            print(f"Caption: {caption.text}, Confidence: {caption.confidence}")

        if detected_objects.objects:
            for obj in detected_objects.objects:
                print(f"Object: {obj.object_property}, Confidence: {obj.confidence}")
    except Exception as e:
        print(f"Exception in processing frame: {e}")

try:
    while True:
        ret, frame = cap.read()
        frame_counter += 1

        if frame_counter % 24 == 0:
            executor.submit(process_frame, frame)

        if not ret:
            print("Failed to grab frame")
            break

        cv2.imshow('Video', frame)

        # Break the loop with the 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    cap.release()
    cv2.destroyAllWindows()