# CV/SLAM Video Analysis Tool

Real-time computer vision and SLAM pipeline for video annotation and target detection.

## Quick Start

```bash
# Clone and setup
git clone https://github.com/DoubleRRL/kombat-vision.git
cd kombat-vision

# Start backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py

# Start frontend (new terminal)
cd frontend
npm install
npm run dev
```

Access at `http://localhost:8080`

## Architecture

- **Frontend**: React/TypeScript interface (`/frontend`)
- **Backend**: FastAPI CV pipeline (`/backend`)
- **Documentation**: Technical specs (`/docs`)

## Performance

- **287 FPS** thermal detection processing
- **Real-time** video annotation and export
- **Multi-class** target detection (personnel, vehicles, aircraft)

## Project Structure

```
/
├── frontend/       # React application
├── backend/        # FastAPI CV pipeline
├── docs/           # Documentation
└── scripts/        # Build utilities
```

See `/docs/README.md` for detailed technical documentation.
