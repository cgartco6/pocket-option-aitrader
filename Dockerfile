# Use official Python image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create secure user
RUN groupadd -r trader && useradd -r -g trader trader

# Set up directories
RUN mkdir /app && chown trader:trader /app
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache/pip

# Copy application
COPY . .

# Set permissions
RUN chown -R trader:trader /app && \
    chmod 700 /app/utilities/security.py

# Switch to non-root user
USER trader

# Run main application
CMD ["python", "main.py"]
