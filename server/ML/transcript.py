import whisper
import os


def transcribe_video(video_path):
    model = whisper.load_model("base")
    result = model.transcribe(video_path)
    return result["text"]


if __name__ == "__main__":
    video_path = "videos/IMG_2227.mp4"  # Change this to your video file path
    transcript = transcribe_video(video_path)
    print(transcript)

