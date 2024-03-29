from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes

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
cap = cv2.VideoCapture(0)

client = ImageAnalysisClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(key)
)

executor = ThreadPoolExecutor(max_workers = 2)

language = "en"
max_descriptions = 3

frame_counter = 0
try:
    while True:
        ret, frame = cap.read()
        frame_counter += 1


        if frame_counter % 24 == 0:

            _, buffer = cv2.imencode('.jpg', frame)
            # Analyze a broader range of visual features
            analysis = computervision_client.analyze_image_in_stream(
                stream,
                visual_features=visual_features,
                language=language
            )

            # Utilize the broader analysis results
            if analysis.description.captions:
                for caption in analysis.description.captions:
                    print(f"Caption: {caption.text}, Confidence: {caption.confidence}")

            if analysis.objects:
                for obj in analysis.objects:
                    print(f"Object: {obj.object_property}, Confidence: {obj.confidence}")

            # Example of using additional features like tags and color
            if analysis.tags:
                print("Tags:", ", ".join([tag.name for tag in analysis.tags]))
            if analysis.color:
                print(f"Dominant Colors: {analysis.color.dominant_colors}")

            # Analyze all visual features from an image stream. This will be a synchronously (blocking) call.
            result = client.analyze_from_url(
                image_url=image_url,
                visual_features=visual_features,
                smart_crops_aspect_ratios=[0.9, 1.33],
                gender_neutral_caption=True,
                language="en"
            )

            # Load image to analyze into a 'bytes' object
            with open("sample.jpg", "rb") as f:
                image_data = f.read()


            # detected_objects = computervision_client.detect_objects_in_stream(frame)

            # Detect objects in the frame
            detected_objects = computervision_client.detect_objects_in_stream(stream)

            # Reset the stream's position to the beginning so we can read from it again
            stream.seek(0)

            # Describe the scene in the frame
            analysis = computervision_client.describe_image_in_stream(stream, max_descriptions, language)

            # Print out the captions and their confidence levels
            for caption in analysis.captions:
                print(f"Caption: {caption.text}, Confidence: {caption.confidence}")

            # Print out the detected objects
            if detected_objects.objects:
                for obj in detected_objects.objects:
                    print(f"Object: {obj.object_property}, Confidence: {obj.confidence}")


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




