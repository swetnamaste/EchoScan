FROM python:3.10-slim

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

# Copy app code
COPY . /app
WORKDIR /app

# Set default command to run the API server
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]