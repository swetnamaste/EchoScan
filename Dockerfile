FROM python:3.10-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
EXPOSE 8080
CMD ["python", "api.py"]