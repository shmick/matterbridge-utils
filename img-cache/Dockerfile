FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY main.py .

# Environment variables will be provided at runtime
ENV R2_ACCOUNT_ID=""
ENV R2_ACCESS_KEY_ID=""
ENV R2_SECRET_ACCESS_KEY=""
ENV R2_BUCKET_NAME=""
ENV CDN_BASE_URL=""

# Expose the port the app runs on
EXPOSE 6161

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "6161"]
