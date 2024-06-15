from ultralytics import YOLO
import os
import zipfile
from glob import glob
import supervision as sv
import numpy as np
from models import Frame, Box
from tempstorage import read_temp
import sqlite3

model_photos = YOLO("weights.pt")
model_videos = YOLO("weights.pt")


def predict_photos(proj_folder):
    output_folder = proj_folder.replace("source/", "prediction/labels/")
    model_photos.predict(proj_folder, save_txt=True, project=proj_folder.replace("source/", ""), name="prediction")
    for file in glob(output_folder + "*"):
        with open(file, "r") as f:
            contents = f.read().replace(" ", ";")
        with open(file, "w") as f:
            f.write(contents)
    zip_file = output_folder.replace("prediction/labels/", "predictions.zip")
    with zipfile.ZipFile(zip_file, 'w') as zf:
        for root, dirs, files in os.walk(output_folder):
            for file in files:
                file_path = os.path.join(root, file)
                zf.write(file_path, os.path.relpath(file_path, output_folder))
    return zip_file


def process_frame(frame: np.ndarray, idx) -> np.ndarray:
    video_id = int(read_temp())
    frameEntity = Frame(
        video_id=video_id,
        number_in_video=idx
    )
    con = sqlite3.connect('DataBase.db')
    frameEntity.save_to_db(con)

    results = model_videos(frame, imgsz=1280, conf=0.5)[0]
    detections = sv.Detections.from_yolov8(results)
    box_annotator = sv.BoxAnnotator(thickness=4, text_thickness=4, text_scale=2)
    labels = [f"{model_videos.names[class_id]} {confidence:0.2f}" for _, _, confidence, class_id, _ in detections]
    frame = box_annotator.annotate(scene=frame, detections=detections, labels=labels)

    for coords, confidence, class_id in zip(detections.xyxy, detections.confidence, detections.class_id):
        boxParams = {
            "frame_id": frameEntity.id,
            "x1": float(coords[0]),
            "y1": float(coords[1]),
            "x2": float(coords[2]),
            "y2": float(coords[3]),
            "object_class": model_videos.names[class_id],
            "confidence": float(confidence)
        }
        boxEntity = Box(**boxParams)
        con = sqlite3.connect('DataBase.db')
        boxEntity.save_to_db(con)
    return frame


def predict_video(video):
    predicted_video_path = video.replace("source", "predictedcvformat")
    sv.process_video(source_path=video, target_path=predicted_video_path, callback=process_frame)
    return predicted_video_path