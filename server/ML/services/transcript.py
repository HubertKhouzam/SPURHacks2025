import whisper
import os
from datetime import datetime


def transcribe_video(video_path, event_q=None):
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
                print(f"\nTimestamp: {timestamp}s")
                print(f"Transcript: {text}")
    
    return result["text"]


if __name__ == "__main__":
    video_path = "videos/IMG_2227.mp4"  # Change this to your video file path
    transcript = transcribe_video(video_path)
    print(transcript)

