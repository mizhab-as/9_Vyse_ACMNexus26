# Dockerfile for NEXUS Backend

FROM python:3.11-slim

WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt ./backend/
COPY ml-engine/requirements.txt ./ml-engine/
COPY data-simulator/requirements.txt ./data-simulator/

RUN pip install --no-cache-dir -r backend/requirements.txt && \
    pip install --no-cache-dir -r ml-engine/requirements.txt && \
    pip install --no-cache-dir -r data-simulator/requirements.txt

# Copy application code
COPY backend ./backend
COPY ml-engine ./ml-engine
COPY data-simulator ./data-simulator
COPY streaming_simulator.py .

# Expose backend port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run backend
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
