#!/usr/bin/env bash
set -e

docker compose down
docker compose pull
docker system prune -f
docker compose up -d
