#!/usr/bin/env bash
set -e

APP_NAME="church-app"
CONTAINER="church-test"
PORT=5000

echo "==> Building image: $APP_NAME"
docker build -t "$APP_NAME" .

echo "==> Stopping any existing container..."
docker rm -f "$CONTAINER" 2>/dev/null || true

echo "==> Starting container: $CONTAINER"
docker run -d \
  --name "$CONTAINER" \
  --shm-size=2g \
  -p "$PORT:5000" \
  -v church_chrome:/tmp/chrome_profile \
  -v church_images:/tmp/images \
  --env-file .env \
  "$APP_NAME"

echo ""
echo "  TKT Outreach Console is running at http://localhost:$PORT"
echo "  Logs: docker logs -f $CONTAINER"
echo "  Stop: ./stop.sh"
