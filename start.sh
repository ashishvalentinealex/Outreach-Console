#!/usr/bin/env bash
set -e

APP="outreach-console"
PORT=5000

# Resolve the directory this script lives in so it works from any working directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Guard: .env must exist
if [ ! -f "$SCRIPT_DIR/.env" ]; then
  echo "ERROR: .env file not found in $SCRIPT_DIR"
  echo "  Copy .env.example to .env and fill in your credentials."
  exit 1
fi

# Guard: Docker must be running
if ! docker info > /dev/null 2>&1; then
  echo "ERROR: Docker is not running. Please start Docker and try again."
  exit 1
fi

# Create volumes on first run if they don't exist
docker volume inspect "${APP}_chrome" > /dev/null 2>&1 || docker volume create "${APP}_chrome"
docker volume inspect "${APP}_images" > /dev/null 2>&1 || docker volume create "${APP}_images"

echo "==> Building image: $APP"
docker build -t "$APP" "$SCRIPT_DIR"

echo "==> Stopping any existing container..."
docker rm -f "$APP" 2>/dev/null || true

echo "==> Starting container: $APP"
docker run -d \
  --name "$APP" \
  --shm-size=2g \
  -p "$PORT:5000" \
  -v "${APP}_chrome:/tmp/chrome_profile" \
  -v "${APP}_images:/tmp/images" \
  --env-file "$SCRIPT_DIR/.env" \
  "$APP"

echo ""
echo "  Outreach Console is running at http://localhost:$PORT"
echo "  Logs: docker logs -f $APP"
echo "  Stop: ./stop.sh"
