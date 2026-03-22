FROM python:3.11-slim

WORKDIR /app

# Install system deps for Playwright
RUN apt-get update && apt-get install -y \
    gcc g++ curl wget gnupg \
    libglib2.0-0 libnss3 libnspr4 libdbus-1-3 libatk1.0-0 \
    libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libatspi2.0-0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 \
    libasound2 libpango-1.0-0 libcairo2 libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium --with-deps

# Copy app code
COPY . .

# Build frontend and copy to app
COPY --from=builder /frontend/dist ./frontend/dist

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
