#!/usr/bin/env bash

CONTAINER="church-test"

echo "==> Stopping container: $CONTAINER"
docker stop "$CONTAINER" 2>/dev/null && echo "  Stopped." || echo "  Container was not running."

echo "==> Removing container: $CONTAINER"
docker rm "$CONTAINER" 2>/dev/null || true

echo "  Done."
