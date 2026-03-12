#!/bin/bash

echo "Starting PostgreSQL service..."

brew services start postgresql@14

echo "Checking if database 'gemsore' exists..."

DB_EXISTS=$(psql -tAc "SELECT 1 FROM pg_database WHERE datname='gemsore'")

if [ "$DB_EXISTS" = "1" ]; then
    echo "Database 'gemsore' already exists."
else
    echo "Creating database 'gemsore'..."
    createdb gemsore
fi

echo "Starting FastAPI application..."

python3 main.py