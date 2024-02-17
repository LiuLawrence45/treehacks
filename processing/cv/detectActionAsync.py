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

executor = ThreadPoolExecutor(max_workers=4)

language = "en"
max_descriptions = 3

frame_counter = 0

# Define a comprehensive list of visual features available
visual_features = [
    VisualFeatureTypes.tags,
    VisualFeatureTypes.objects,
    VisualFeatureTypes.description,
    VisualFeatureTypes.brands,
    VisualFeatureTypes.categories,  # Provides categorization of the image content
    VisualFeatureTypes.adult,       # Detects adult content
    VisualFeatureTypes.color,       # Identifies dominant colors, color scheme
    VisualFeatureTypes.faces,       # Detects faces and guesses age and gender
    VisualFeatureTypes.image_type   # Identifies type of image (clipart, line drawing, etc.)
]

def process_frame(frame):
    try:
        _, buffer = cv2.imencode('.jpg', frame)
        stream = BytesIO(buffer)

        # Analyze the frame for the specified visual features
        analysis = computervision_client.analyze_image_in_stream(stream, visual_features=visual_features)

        # Process and print descriptions
        if analysis.description.captions:
            for caption in analysis.description.captions:
                print(f"Caption: {caption.text}, Confidence: {caption.confidence}")

        # Process and print tags, objects, and brands
        if analysis.tags:
            print("Tags:", ', '.join([tag.name for tag in analysis.tags]))
        if analysis.objects:
            print("Objects:", ', '.join([obj.object_property for obj in analysis.objects]))
        if analysis.brands:
            print("Brands:", ', '.join([brand.name for brand in analysis.brands]))

        # Additional features like categories, adult content, color, faces, and image type can be processed here
        # Example for categories
        if analysis.categories:
            print("Categories:", ', '.join([category.name for category in analysis.categories]))

        print("------------------")

    except Exception as e:
        print(f"Exception in processing frame: {e}")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        # Process every 24th frame to reduce load
        if int(cap.get(cv2.CAP_PROP_POS_FRAMES)) % 24 == 0:
            executor.submit(process_frame, frame)

        cv2.imshow('Video', frame)

        # Break the loop with the 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    cap.release()
    cv2.destroyAllWindows()