#!/bin/bash
# Startup script for Tobby Downloader Bot

echo "Starting Tobby Downloader Bot..."

# Check if we're in webhook mode or polling mode
if [ "$WEBHOOK_MODE" = "true" ]; then
    echo "Running in webhook mode..."
    python app.py
else
    echo "Running in polling mode..."
    python app.py
fi