"""
FastAPI Backend for CV/SLAM Video Analysis
Minimal working backend that will integrate kombat-drone CV pipeline
"""
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import time
import asyncio
from typing import Dict, Any, List
import json

from cv_pipeline.video_processor import VideoProcessor

app = FastAPI(title="CV/SLAM Analysis API", version="1.0.0")

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8080"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state for processing
processing_state = {
    "is_processing": False,
    "current_video": None,
    "progress": 0,
    "detections": [],
    "slam_data": None
}

# Global video processor instance
video_processor = VideoProcessor()

# Progress callback for video processing
async def update_progress(progress_data: Dict[str, Any]):
    """Update global processing state with progress data"""
    processing_state["progress"] = progress_data.get("progress", 0)
    processing_state["detections"] = progress_data.get("detections_count", 0)
    print(f"Progress: {progress_data.get('progress', 0):.1f}% - Frame {progress_data.get('current_frame', 0)}/{progress_data.get('total_frames', 0)} - Detections: {progress_data.get('detections_count', 0)}")

video_processor.progress_callback = update_progress

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "CV/SLAM Analysis API is running", "status": "operational"}

@app.post("/upload-video")
async def upload_video(file: UploadFile = File(...)):
    """
    Upload video file for CV/SLAM analysis
    Baby Step: Just accept and validate the file for now
    """
    # Input validation
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check file type
    allowed_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: {file_ext}. Allowed: {allowed_extensions}"
        )
    
    # Check file size (limit to 500MB for now)
    max_size = 500 * 1024 * 1024  # 500MB
    file_size = 0
    content = await file.read()
    file_size = len(content)
    
    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {file_size / 1024 / 1024:.1f}MB. Max: 500MB"
        )
    
    # Save file temporarily (in production, use proper storage)
    upload_dir = "backend/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Update global state
    processing_state["current_video"] = {
        "filename": file.filename,
        "path": file_path,
        "size": file_size,
        "uploaded_at": time.time()
    }
    processing_state["progress"] = 0
    processing_state["detections"] = []
    processing_state["slam_data"] = None
    
    return {
        "message": "Video uploaded successfully",
        "filename": file.filename,
        "size": file_size,
        "status": "ready_for_processing"
    }

@app.post("/start-processing")
async def start_processing():
    """
    Start CV/SLAM processing on uploaded video
    Now uses actual thermal detection from kombat-drone pipeline
    """
    if not processing_state["current_video"]:
        raise HTTPException(status_code=400, detail="No video uploaded")

    if processing_state["is_processing"]:
        raise HTTPException(status_code=400, detail="Processing already in progress")

    processing_state["is_processing"] = True
    processing_state["progress"] = 0
    processing_state["detections"] = []

    video_path = processing_state["current_video"]["path"]

    # Start processing in background
    asyncio.create_task(process_video_background(video_path))

    return {
        "message": "CV/SLAM processing started with thermal detection",
        "video": processing_state["current_video"]["filename"],
        "status": "processing",
        "pipeline": "kombat-drone thermal detection"
    }

async def process_video_background(video_path: str):
    """Background task for video processing"""
    try:
        print(f"Starting CV processing on: {video_path}")
        result = await video_processor.process_video(video_path)

        # Update final state
        processing_state["is_processing"] = False
        processing_state["progress"] = 100

        if result["status"] == "completed":
            # Store detection results
            all_detections = video_processor.get_all_detections()
            processing_state["detections"] = len([d for frame in all_detections for d in frame["detections"]])
            processing_state["slam_data"] = result["metrics"]

            print(f"Processing completed: {result['metrics']['total_detections']} detections found")
        else:
            print(f"Processing failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"Background processing error: {e}")
        processing_state["is_processing"] = False
        processing_state["progress"] = 0

@app.get("/processing-status")
async def get_processing_status():
    """Get current processing status and metrics"""
    return {
        "is_processing": processing_state["is_processing"],
        "progress": processing_state["progress"],
        "current_video": processing_state["current_video"],
        "detections_count": len(processing_state["detections"]),
        "slam_status": "active" if processing_state["slam_data"] else "inactive"
    }

@app.get("/detections")
async def get_detections():
    """Get current detection results"""
    if not video_processor.detections_history:
        return {
            "detections": [],
            "total_count": 0,
            "video": processing_state["current_video"]["filename"] if processing_state["current_video"] else None,
            "summary": {}
        }

    # Get all detections from all frames
    all_frame_detections = []
    total_detections = 0

    for frame_data in video_processor.detections_history:
        frame_detections = frame_data.get("detections", [])
        all_frame_detections.append({
            "frame_number": frame_data["frame_number"],
            "timestamp": frame_data["timestamp"],
            "detections": frame_detections,
            "count": len(frame_detections)
        })
        total_detections += len(frame_detections)

    # Create summary by class
    class_summary = {}
    for frame_data in video_processor.detections_history:
        for detection in frame_data.get("detections", []):
            class_name = detection.get("class_name", "unknown")
            if class_name not in class_summary:
                class_summary[class_name] = {"count": 0, "max_confidence": 0.0}
            class_summary[class_name]["count"] += 1
            class_summary[class_name]["max_confidence"] = max(
                class_summary[class_name]["max_confidence"],
                detection.get("confidence", 0.0)
            )

    return {
        "detections": all_frame_detections[-10:] if len(all_frame_detections) > 10 else all_frame_detections,  # Last 10 frames
        "total_count": total_detections,
        "frames_processed": len(video_processor.detections_history),
        "video": processing_state["current_video"]["filename"] if processing_state["current_video"] else None,
        "summary": class_summary,
        "performance": video_processor.performance_metrics
    }

@app.get("/detections/frame/{frame_number}")
async def get_frame_detections(frame_number: int):
    """Get detections for a specific frame"""
    frame_data = video_processor.get_detections_for_frame(frame_number)
    if not frame_data:
        raise HTTPException(status_code=404, detail=f"No data found for frame {frame_number}")

    return frame_data

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
