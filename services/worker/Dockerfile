FROM python:3.12-slim

WORKDIR /app

# Copy shared utilities first
COPY ../shared /app/shared

# Copy worker files
COPY requirements.txt .
COPY *.py .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Non-root user for security
RUN useradd -m -u 1000 worker && chown -R worker:worker /app
USER worker

EXPOSE 8001

CMD ["python", "main.py"]
