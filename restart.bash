#!/bin/bash

service_name="scraper"  # Name of the service in docker-compose.yml

echo "Stopping and removing the $service_name service..."
docker-compose stop $service_name
docker-compose rm -f $service_name

echo "Rebuilding and starting the $service_name service..."
docker-compose up --build -d $service_name
