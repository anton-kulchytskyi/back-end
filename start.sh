#!/bin/bash

# Exit on error
set -e

echo "Starting application..."

# Here you can add automatic migrations in the future
# Example: alembic upgrade head

# Run the FastAPI application
python -m app.main