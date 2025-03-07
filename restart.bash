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
docker rm -f Doctorise_scraper_container  # Ensure the container is fully removed

echo "Restarting the scraper without rebuilding..."
docker-compose -f compose.yml up -d $service_name  # Restart without rebuilding

echo "Ensuring all services are running..."
docker-compose -f compose.yml up -d
