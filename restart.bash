#!/bin/bash

container_name="Doctorise_scraper_container"

echo "Restarting $container_name..."
docker-compose restart scraper
