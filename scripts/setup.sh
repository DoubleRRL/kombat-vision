#!/bin/bash
# Setup script for CV/SLAM Video Analysis Tool

echo "Setting up CV/SLAM Video Analysis Tool..."

# Setup frontend
echo "Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Setup backend
echo "Setting up backend environment..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

echo "Setup complete!"
echo ""
echo "To start the application:"
echo "  npm run dev"
echo ""
echo "Or start components separately:"
echo "  Frontend: cd frontend && npm run dev"
echo "  Backend:  cd backend && source venv/bin/activate && python main.py"
