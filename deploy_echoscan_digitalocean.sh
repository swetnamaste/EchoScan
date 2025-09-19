#!/bin/bash

set -e

REPO_URL="https://github.com/swetnamaste/EchoScan.git"
APP_DIR="$HOME/EchoScan"
DOCKER_IMAGE="echoscan"
CONTAINER_NAME="echoscan_prod"
PORT=8000

# 1. Clone the latest code
if [ -d "$APP_DIR" ]; then
    echo "==> Repo exists, pulling latest..."
    cd "$APP_DIR"
    git pull
else
    echo "==> Cloning EchoScan repo..."
    git clone $REPO_URL "$APP_DIR"
    cd "$APP_DIR"
fi

# 2. Run tests
echo "==> Running tests..."
pytest || { echo "Tests failed!"; exit 1; }
echo "==> Tests passed."

# 3. Build Docker image
echo "==> Building Docker image..."
docker build -t $DOCKER_IMAGE .

# 4. Stop and remove any existing container
if docker ps -a --format '{{.Names}}' | grep -Eq "^$CONTAINER_NAME$"; then
    echo "==> Stopping and removing existing container..."
    docker stop $CONTAINER_NAME || true
    docker rm $CONTAINER_NAME || true
fi

# 5. Run the new container with environment
echo "==> Starting new container..."
docker run -d --name $CONTAINER_NAME -p $PORT:8000 --env-file .env $DOCKER_IMAGE

sleep 10

# 6. Smoke Test: Trigger webhook and UI
echo "==> Smoke Test: triggering quarantine event..."
curl -X POST "http://localhost:${PORT}/api/scan" \
  -H "Content-Type: application/json" \
  -d '{"input":"QUARANTINE_TRIGGER"}'

echo "==> Manual Step: Open http://<YOUR_DROPLET_IP>:${PORT} in your browser."
echo "==> Check for confetti/balloon verdicts and verify webhook/Jira delivery."
echo "==> Monitor container logs: docker logs $CONTAINER_NAME"

echo "==> To clean up the deployment:"
echo "docker stop $CONTAINER_NAME && docker rm $CONTAINER_NAME"