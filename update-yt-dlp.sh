#!/bin/bash
# docker compose exec yt-music-download pip install --upgrade yt-dlp

PROJECT_DIR="/home/dani/docker" 
LOG_FILE="$PROJECT_DIR/yt_dlp_update.log"

# Function to log messages to both stdout and the log file
log_message() {
  echo "$1" | tee -a "$LOG_FILE"
}

# Exit immediately if a command exits with a non-zero status.
set -e 

mkdir -p "$(dirname "$LOG_FILE")" && touch "$LOG_FILE" || {
  echo "ERROR: Cannot write to log file $LOG_FILE. Check permissions." >&2
  exit 1
}

# Truncate the log file to zero length (overwrite) before writing new logs
> "$LOG_FILE"

log_message "Starting yt-dlp update script at $(date)"

# Navigate to the project directory
cd "$PROJECT_DIR" || { log_message "Failed to cd into $PROJECT_DIR"; exit 1; }

log_message "Running docker compose build --no-cache..."
/usr/bin/docker compose build --no-cache yt-music-download 2>&1 | tee -a "$LOG_FILE"

log_message "Running docker compose up -d..."
/usr/bin/docker compose up -d --remove-orphans yt-music-download 2>&1 | tee -a "$LOG_FILE"

log_message "Script finished successfully at $(date)"

exit 0

