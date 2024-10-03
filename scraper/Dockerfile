# Use a slim version of Python
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install system dependencies for Playwright (only Chromium-related)
RUN apt-get update && apt-get install -y \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libxshmfence1 \
    libxdamage1 \
    libxfixes3 \
    fonts-liberation \
    --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright itself
RUN pip install --no-cache-dir playwright

# Install only Chromium (skip WebKit and Firefox)
RUN playwright install chromium

# Copy the rest of the application files
COPY . /app

# Command to run the scraper
CMD ["python", "scrape_main.py"]
