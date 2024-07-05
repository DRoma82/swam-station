#!/bin/bash

# Count the number of running docker containers
running_containers=$(docker ps -q | wc -l)

# If there are running containers, inhibit sleep
if [ "$running_containers" -ne 0 ]; then
    exit 1
else
    exit 0
fi
