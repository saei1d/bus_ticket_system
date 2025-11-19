#!/bin/bash
# Database initialization script

echo "Waiting for PostgreSQL to be ready..."
sleep 5

echo "Running Alembic migrations..."
alembic upgrade head

echo "Database initialized successfully!"

