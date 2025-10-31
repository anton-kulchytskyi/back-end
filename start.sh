#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting application..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
until pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER"; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done
echo "✅ PostgreSQL is ready!"

# Wait for Redis to be ready
echo "⏳ Waiting for Redis..."
until redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping 2>/dev/null; do
  echo "Redis is unavailable - sleeping"
  sleep 1
done
echo "✅ Redis is ready!"

# Run database migrations automatically
echo "🔄 Running database migrations..."
alembic upgrade head
echo "✅ Migrations completed!"

# Run the FastAPI application
echo "🎯 Starting FastAPI application..."
python -m app.main