#!/bin/bash
set -e

# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "Starting Database..."
docker compose up -d db

echo "Waiting for DB to be healthy..."
sleep 5 # Simple wait, ideally check health

echo "Running Migrations..."
alembic upgrade head

echo "Seeding Database..."
python seed.py

echo "Starting Application..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
APP_PID=$!

echo "Waiting for App to start..."
sleep 5

echo "Running Verification Script..."
python verification_script.py

echo "Stopping App..."
kill $APP_PID
