# Use Python base image with AMD64 architecture
FROM --platform=linux/amd64 python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data (if needed)
RUN python -c "import nltk; nltk.download('stopwords')"

# Copy your code
COPY pdf_extractor.py .
COPY main.py .

# Create input and output directories
RUN mkdir -p /app/input /app/output

# Set the command to run your application
CMD ["python", "main.py"]