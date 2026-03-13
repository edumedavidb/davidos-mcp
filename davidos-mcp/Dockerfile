FROM python:3.11-slim

WORKDIR /app

# Install dependencies (paths relative to repo root since that's the build context)
COPY davidos-mcp/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY davidos-mcp/app/ ./app/
COPY davidos-mcp/main.py .
COPY davidos-mcp/pyproject.toml .

# Copy DavidOS content
COPY davidos-mcp/davidos/ ./davidos/

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the server
CMD ["python", "-m", "uvicorn", "app.mcp_server:app", "--host", "0.0.0.0", "--port", "8000"]
