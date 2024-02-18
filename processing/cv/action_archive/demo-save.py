

import cv2
import numpy as np
import os
import uuid

# Open the video file
# cap = cv2.VideoCapture('processing/cv/requirements.mp4')

cap = cv2.VideoCapture(0)

# Get the frame width and height
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Create a video writer object
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('processing/cv/output.mp4', fourcc, 20.0, (width, height))

# Write the video frames

while True:
    ret, frame = cap.read()
    if not ret:
        break

    cv2.imshow("Video", frame)
    out.write(frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
# while cap.isOpened():
#     ret, frame = cap.read()
#     if not ret:
#         break

#     out.write(frame)

# Release the video capture and writer objects
cap.release()
out.release()

# Close all windows
cv2.destroyAllWindows()