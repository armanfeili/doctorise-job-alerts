#!/bin/bash

# Define project directory
PROJECT_DIR="/opt/doctorise-job-alerts"

# Ensure we are in the correct directory
cd "$PROJECT_DIR" || { echo "Error: Failed to change directory to $PROJECT_DIR"; exit 1; }

# Define service name
service_name="scraper"

echo "Stopping and removing the $service_name service..."
docker-compose -f compose.yml stop $service_name
docker-compose -f compose.yml rm -f $service_name

echo "Rebuilding and starting the $service_name service..."
docker-compose -f compose.yml up --build -d $service_name

echo "Ensuring all services are running..."
docker-compose -f compose.yml up -d  # Ensures all services are running
