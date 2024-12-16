import os
import io
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter, File, UploadFile, HTTPException
from ultralytics import YOLO
from fastapi.responses import JSONResponse
from PIL import Image
import numpy as np
from pathlib import Path
from app.api.v1.controller.yolo import yolo_prediction
from prometheus_client import Gauge, Histogram

image_brightness_metric = Gauge("image_brightness", 
                                "Brightness of processed images")

brightness_histogram = Histogram(
    'image_brightness_histogram',
    'Histogram of image brightness',
    buckets=[100, 200, 255] 
)

LOCAL_ARTIFACTS = Path("/DATA/artifacts")
LOCAL_CAPTURED = Path("/DATA/captured/yolo")

UPLOAD_DIR = LOCAL_CAPTURED / "uploads"
ANNOTATED_DIR = LOCAL_CAPTURED / "annotated"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(ANNOTATED_DIR, exist_ok=True)


def load_model(model_path: str) -> YOLO:
    """Load YOLO model from file path"""
    try:
        model = YOLO(model_path)
        return model
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading model: {str(e)}")


models = {}
@asynccontextmanager
async def lifespan(app: FastAPI):
    model_path = LOCAL_ARTIFACTS / "yolo" / "best.pt"
    models["yolo"] = load_model(model_path)
    yield
    models.clear()

router = APIRouter(lifespan=lifespan)


@router.post("/detect/")
async def detect_objects(file: UploadFile = File(...)):
    """
    Endpoint for object detection on uploaded image
    
    :param file: Uploaded image file
    :return: JSON response with detection results and file paths
    """
    try:
        # Generate unique filename
        original_filename = file.filename
        unique_filename = f"{uuid.uuid4()}_{original_filename}"
        
        # Full paths for saving
        original_filepath = os.path.join(UPLOAD_DIR, unique_filename)
        annotated_filepath = os.path.join(ANNOTATED_DIR, f"annotated_{unique_filename}")
        
        # Read and save original image
        contents = await file.read()
        with open(original_filepath, "wb") as f:
            f.write(contents)
        
        # Open image for detection
        image = Image.open(io.BytesIO(contents))

        grayscale_image = image.convert("L")
        image_array = np.asarray(grayscale_image)
        brightness = image_array.mean()

        image_brightness_metric.set(brightness)
        brightness_histogram.observe(brightness)
        
        # Perform object detection
        detections = yolo_prediction(
            models["yolo"],
            image,
            annotated_filepath
        )
        
        return JSONResponse(content={
            'detections': detections,
            'total_objects': len(detections),
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection error: {str(e)}")
