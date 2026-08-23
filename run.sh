#!/bin/bash

# Telconnect - Start Backend and Frontend

# Move to project root
cd "$(dirname "$0")" || exit 1

# Stop both servers when this script exits
trap 'kill 0' EXIT

echo "======================================"
echo "Starting Telconnect..."
echo "======================================"

# Start Backend
echo "Starting backend on http://localhost:8000..."
(
    cd backend || exit 1

    if [ ! -f ".venv/bin/python" ]; then
        echo "ERROR: Backend virtual environment not found."
        echo "Run: cd backend && python3 -m venv .venv"
        exit 1
    fi

    .venv/bin/python -m uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000
) &

# Start Frontend
echo "Starting frontend on http://localhost:5173..."
(
    cd frontend || exit 1
    npm run dev
) &

echo "======================================"
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "======================================"

# Keep both servers running
wait