# CV/SLAM Video Analysis Tool

Real-time computer vision and SLAM pipeline for video annotation and target detection. Integrates thermal detection algorithms from the kombat-drone project with a web-based interface for video analysis and export.

## Architecture

**Frontend**: React/TypeScript with real-time video player and annotation display
**Backend**: FastAPI with OpenCV-based thermal detection pipeline
**CV Pipeline**: Temperature-based target detection (287 FPS processing speed)

## Performance Metrics

- **Detection Speed**: 287 FPS on M2 MacBook Air
- **Target Classification**: Personnel, vehicles, aircraft, equipment
- **Confidence Scoring**: Temperature-based thermal signature analysis
- **Processing**: Real-time frame-by-frame analysis with live progress updates

## Quick Start

```bash
# Clone repository
git clone https://github.com/DoubleRRL/kombat-vision.git
cd kombat-vision

# Install frontend dependencies
npm install

# Setup backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start backend (terminal 1)
cd backend && source venv/bin/activate && python main.py

# Start frontend (terminal 2)
npm run dev
```

Access the application at `http://localhost:8080`

## CV Pipeline Features

- **Thermal Detection**: Temperature thresholding with contour analysis
- **Multi-class Classification**: Hostile personnel, vehicles, aircraft threats
- **Real-time Processing**: Async video processing with live status updates
- **Performance Monitoring**: FPS tracking, confidence scoring, detection counts
- **Export Capabilities**: Annotated video output with embedded detection data

## API Endpoints

- `POST /upload-video` - Upload video files for analysis
- `POST /start-processing` - Trigger CV pipeline processing
- `GET /processing-status` - Real-time processing progress
- `GET /detections` - Detection results and performance metrics
- `GET /detections/frame/{n}` - Frame-specific detection data

## Technology Stack

**Frontend**: React, TypeScript, Tailwind CSS, shadcn/ui
**Backend**: FastAPI, OpenCV, NumPy
**CV Pipeline**: Temperature-based detection algorithms from kombat-drone project
