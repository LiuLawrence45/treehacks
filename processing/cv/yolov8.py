from ultralytics import YOLO

model = YOLO('processing/cv/smallest-YOLO.pt')

results = model(source = 0, show = True, conf = 0.3, save = True)