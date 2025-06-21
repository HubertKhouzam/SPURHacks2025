#!/bin/bash

# Ask user for the stream key
read -p "Enter stream key (e.g., 'ok'): " STREAM_KEY

if [ -z "$STREAM_KEY" ]; then
  echo "❌ No stream key entered. Exiting."
  exit 1
fi

# Compose full RTMP URL
STREAM_URL="rtmp://localhost:1935/live/$STREAM_KEY"

# Kill any previous media server or FFmpeg instances
pkill -f media-server.js
pkill -f ffmpeg

# Pull latest code and install deps
git pull origin main
npm install

# Start Node.js RTMP server
nohup node media-server.js > media.log 2>&1 &
echo "🚀 Media server started on rtmp://localhost:1935/live/$STREAM_KEY"

sleep 5

# Check if --buffer flag was passed
if [[ "$1" == "--buffer" ]]; then
  # Create media directory if it doesn't exist
  mkdir -p media

  # Start FFmpeg rolling buffer into ./media
  nohup ffmpeg -i "$STREAM_URL" \
    -c copy -f segment -segment_time 6 -segment_wrap 10 \
    -reset_timestamps 1 media/out%02d.mp4 > ffmpeg.log 2>&1 &

  echo "🎥 Rolling buffer is running and saving to ./media/"
else
  echo "ℹ️ Buffer not started. Run './run.sh --buffer' to enable rolling buffer."
fi
