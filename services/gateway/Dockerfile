FROM python:3.12-slim

WORKDIR /app

# Copy shared utilities first
COPY ../shared /app/shared

# Copy gateway files
COPY requirements.txt .
COPY *.py .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Non-root user for security
RUN useradd -m -u 1000 gateway && chown -R gateway:gateway /app
USER gateway

EXPOSE 8000

CMD ["python", "main.py"]
