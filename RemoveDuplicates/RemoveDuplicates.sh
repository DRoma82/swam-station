#!/bin/bash

# Define paths for Sonarr and Radarr directories
SONARR_SOURCE="/mnt/seagate/downloads/complete/Sonarr/"
SONARR_DESTINATION="/mnt/seagate/media/sonarr/"

RADARR_SOURCE="/mnt/seagate/downloads/complete/Radarr/"
RADARR_DESTINATION="/mnt/seagate/media/radarr/"

# Run the Python script for Sonarr
echo "Processing Sonarr directories..."
python main.py "$SONARR_SOURCE" "$SONARR_DESTINATION"

# Run the Python script for Radarr
echo "Processing Radarr directories..."
python main.py "$RADARR_SOURCE" "$RADARR_DESTINATION"

echo "Processing complete."
