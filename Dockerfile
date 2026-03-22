# Multi-stage build: Build React frontend, then serve from FastAPI

# ── Stage 1: Build React frontend ────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

# ── Stage 2: FastAPI backend + serve frontend ─────────────────────
FROM python:3.11-slim
WORKDIR /app

# System dependencies (Playwright + scraping libs)
RUN apt-get update && apt-get install -y \
    gcc g++ curl wget gnupg \
    libglib2.0-0 libnss3 libnspr4 libdbus-1-3 libatk1.0-0 \
    libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libatspi2.0-0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 \
    libasound2 libpango-1.0-0 libcairo2 libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# ── Copy requirements FIRST so layer cache is busted on any change ──
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (optional, non-fatal)
RUN playwright install chromium --with-deps || true

# Copy all backend code
COPY backend/ .

# Copy built frontend dist
COPY --from=builder /frontend/dist ./frontend/dist

EXPOSE 8080

# Shell form so $PORT is expanded by Railway
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1
