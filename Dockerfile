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

# Download IRS PDF form templates (names must match form_ids in code)
RUN python -c "\
from urllib.request import urlretrieve; \
from pathlib import Path; \
d = Path('/app/app/pdf/templates'); d.mkdir(parents=True, exist_ok=True); \
forms = { \
    'form_1040': 'https://www.irs.gov/pub/irs-pdf/f1040.pdf', \
    'schedule_a': 'https://www.irs.gov/pub/irs-pdf/f1040sa.pdf', \
    'schedule_b': 'https://www.irs.gov/pub/irs-pdf/f1040sb.pdf', \
    'schedule_d': 'https://www.irs.gov/pub/irs-pdf/f1040sd.pdf', \
    'schedule_1': 'https://www.irs.gov/pub/irs-pdf/f1040s1.pdf', \
    'schedule_2': 'https://www.irs.gov/pub/irs-pdf/f1040s2.pdf', \
    'schedule_3': 'https://www.irs.gov/pub/irs-pdf/f1040s3.pdf', \
    'form_8949': 'https://www.irs.gov/pub/irs-pdf/f8949.pdf', \
    'schedule_8812': 'https://www.irs.gov/pub/irs-pdf/f1040s8.pdf', \
    'form_8863': 'https://www.irs.gov/pub/irs-pdf/f8863.pdf', \
    'form_8880': 'https://www.irs.gov/pub/irs-pdf/f8880.pdf', \
}; \
[print(f'Downloading {n}...') or urlretrieve(u, d/f'{n}.pdf') for n,u in forms.items()]; \
print('Done')"

# Create data directories
RUN mkdir -p /app/data /app/data/uploads

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
