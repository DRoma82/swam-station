#!/bin/bash

docker compose down
docker compose pull
docker system prune -f
docker compose up -d
