# --- Stage 1: Builder ---
FROM python:3.11-alpine as builder

WORKDIR /app

# Install build dependencies for Python packages (gcc, musl, etc.)
RUN apk add --no-cache gcc musl-dev libffi-dev

COPY requirements.txt .

# Install dependencies into a local folder
RUN pip install --user --no-cache-dir -r requirements.txt

# --- Stage 2: Final Runtime ---
FROM python:3.11-alpine

WORKDIR /app

# Copy only the installed packages from the builder stage
COPY --from=builder /root/.local /root/.local
COPY . .

# Ensure the local bin is in the PATH so uvicorn can be found
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]