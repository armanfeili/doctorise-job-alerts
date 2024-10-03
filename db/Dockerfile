# db/Dockerfile

FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install SQLite and other necessary Python packages
RUN apt-get update && apt-get install -y sqlite3 libsqlite3-dev

# Copy the initialization scripts or any schema files (if any)
COPY . /app

# Run SQLite, creating the jobs.db database file (optional, depends on your workflow)
CMD ["sqlite3", "/var/lib/db/jobs.db"]
