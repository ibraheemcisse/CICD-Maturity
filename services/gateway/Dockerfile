FROM python:3.12-slim

WORKDIR /app

# Copy shared utilities
COPY services/shared /app/shared

# Copy gateway service files
COPY services/gateway/requirements.txt /app/
COPY services/gateway/*.py /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Non-root user for security
RUN useradd -m -u 1000 gateway && chown -R gateway:gateway /app
USER gateway

EXPOSE 8000

CMD ["python", "main.py"]
