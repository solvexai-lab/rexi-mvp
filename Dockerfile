# REXI Production Dockerfile — single container serving API + built frontend
# Build: docker build -t rexi .
# Run:   docker run -p 8000:8000 --env-file .env rexi

# ── Stage 1: Build frontend ──
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Python backend ──
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies for PyMuPDF
RUN apt-get update && apt-get install -y \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy backend code
COPY backend/ ./

# Copy vendor modules (contractguard, legal_redline, etc.)
COPY vendor/ ./vendor/
# Each repo root must be on PYTHONPATH so nested packages are importable
ENV PYTHONPATH=/app/vendor/contractguard:/app/vendor/legal-redline:/app/vendor/marker:/app/vendor/multi-agent-contract/apps/api:/app/vendor/graphrag-contract:/app/vendor/agentic-rag:/app/vendor/PageIndex

# Copy built frontend from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Ensure uploads directory exists
RUN mkdir -p /app/uploads

EXPOSE 8000
COPY backend/start.sh ./start.sh
RUN chmod +x ./start.sh
CMD ["./start.sh"]
