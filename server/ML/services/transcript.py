import whisper
import os
import logging
from datetime import datetime


def transcribe_video(video_path, event_q=None):
    logger = logging.getLogger('transcript')
    model = whisper.load_model("base")
    result = model.transcribe(video_path)
    
    # Process segments with timestamps if available
    if "segments" in result:
        for segment in result["segments"]:
            timestamp = str(int(segment["start"]))  # Get timestamp in seconds
            text = segment["text"].strip()
            
            if event_q:
                event_q.put({
                    "type": "transcript",
                    "timestamp": datetime.now(),
                    "text": text,
                    "video_timestamp": timestamp
                })
            else:
                logger.info(f"Timestamp: {timestamp}s")
                logger.info(f"Transcript: {text}")
    
    return result["text"]


if __name__ == "__main__":
    # Set up basic logging for standalone usage
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    video_path = "videos/IMG_2227.mp4"  # Change this to your video file path
    transcript = transcribe_video(video_path)
    logging.getLogger('transcript').info(transcript)

