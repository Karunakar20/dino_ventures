#!/bin/bash
set -e

# Wait for DB?
# We can use wait-for-it or just sleep/retry in python. 
# Docker Compose healthcheck handles dependency start order, but not necessarily "ready for connections".
# Alembic usually retries or we can add a simple python waiter.

echo "Running migrations..."
export PYTHONPATH=$PYTHONPATH:.
alembic upgrade head

echo "Seeding database..."
python seed.py

echo "Starting server..."
uvicorn main:app --host 0.0.0.0 --port 8000
