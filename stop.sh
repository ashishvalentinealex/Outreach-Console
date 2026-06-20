#!/usr/bin/env bash

APP="outreach-console"

echo "==> Stopping container: $APP"
docker stop "$APP" 2>/dev/null && echo "  Stopped." || echo "  Container was not running."

echo "==> Removing container: $APP"
docker rm "$APP" 2>/dev/null || true

echo "  Done."
