#!/bin/bash
# Script to run Alembic migrations in Docker container

echo "Running Alembic migrations..."
alembic upgrade head
echo "Migrations completed!"

