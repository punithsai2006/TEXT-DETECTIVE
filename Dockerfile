# ==========================================
# Stage 1: Build React Frontend
# ==========================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# ==========================================
# Stage 2: Python Backend & Static Server
# ==========================================
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python requirements
COPY requirements.txt ./
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application, data, and scripts
COPY backend/ ./backend/
COPY data/ ./data/
COPY docs/ ./docs/
COPY scripts/ ./scripts/

# Copy built frontend from Stage 1 into frontend/dist
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Seed demo benchmark cases
RUN python scripts/seed_demo_cases.py

# Default environment configuration
ENV PORT=10000
ENV HOST=0.0.0.0
ENV LLM_PROVIDER=mock
ENV DEMO_MODE=true
ENV STORAGE_DIR=storage

EXPOSE 10000

# Start server using Render's $PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000} --app-dir backend"]
