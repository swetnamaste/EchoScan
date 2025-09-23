FROM python:3.10-slim

# Set environment variables
ENV PIP_ROOT_USER_ACTION=ignore
ENV PORT=8080

WORKDIR /app
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port
EXPOSE 8080

# Run FastAPI application
CMD ["python", "api.py"]