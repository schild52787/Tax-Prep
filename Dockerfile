# Combined Dockerfile for Railway deployment
# Builds frontend, copies into backend, serves everything from FastAPI

# Stage 1: Build frontend
FROM node:22-slim AS frontend-build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Backend + serve frontend static files
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy backend code
COPY backend/ .

# Install Python dependencies
RUN pip install --no-cache-dir .

# Copy built frontend into static/ directory
COPY --from=frontend-build /app/dist ./static

# Create data directories
RUN mkdir -p /app/data /app/data/uploads

EXPOSE 8000

ENV PORT=8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]
