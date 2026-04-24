# --- Stage 1: Builder ---
FROM python:3.11-alpine as builder

# Set working directory
WORKDIR /app

# Install build dependencies
# gcc and musl-dev are required to compile certain python wheels (like kafka-python)
RUN apk add --no-cache gcc musl-dev libffi-dev

# Copy only requirements to leverage Docker cache
COPY requirements.txt .

# Install dependencies with high timeout and retries to prevent WSL2 network drops
RUN pip install --user --no-cache-dir \
    --default-timeout=1000 \
    --retries 10 \
    -r requirements.txt

# --- Stage 2: Final Runtime ---
FROM python:3.11-alpine

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PATH=/root/.local/bin:$PATH

WORKDIR /app

# Copy only the installed packages from the builder stage
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Expose the FastAPI port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]