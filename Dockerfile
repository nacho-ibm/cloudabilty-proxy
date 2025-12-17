# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY cloudability_proxy.py .

# Expose port (Code Engine will use PORT env variable)
EXPOSE 8080

# Set environment variable for production
ENV PORT=8080

# Run the application with Gunicorn (production-ready)
CMD gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 cloudability_proxy:app
