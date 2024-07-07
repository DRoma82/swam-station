#!/usr/bin/env bash
set -e

docker compose --env-file .secrets down
docker compose --env-file .secrets pull
docker system prune -f
docker compose --env-file .secrets up -d
