# Use official Python runtime
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (none needed for basic python args, but git sometimes helpful)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY src /app/src
COPY data /app/data
# Note: In production, 'data' might be a volume mapping to persist sessions.

# Expose Streamlit port
EXPOSE 8501

# Set env vars
ENV PYTHONPATH=/app

# Command to run
CMD ["streamlit", "run", "src/ui/app.py", "--server.address=0.0.0.0"]
