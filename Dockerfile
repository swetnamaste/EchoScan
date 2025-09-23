FROM python:3.10-slim
ENV PIP_ROOT_USER_ACTION=ignore
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "api.py"]