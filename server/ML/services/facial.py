from deepface import DeepFace
import cv2
import time
from collections import Counter

def analyze_video_emotion(video_path):
    start_time = time.perf_counter()         # ⏱️ start the timer

    print("----------- Emotion Analysis Started -----------")
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    emotions = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % 10 == 0:            # sample every 10th frame
            try:
                result = DeepFace.analyze(
                    frame,
                    actions=['emotion'],
                    enforce_detection=False
                )
                emotions.append(result[0]['dominant_emotion'])
            except Exception:
                pass

        frame_count += 1

    cap.release()

    elapsed = time.perf_counter() - start_time   # ⏱️ stop the timer
    print("Most common emotions:", Counter(emotions).most_common())
    print(f"Total run time: {elapsed:.2f} seconds")

if __name__ == "__main__":
    video_path = "output2.mp4"  # Replace with your video file path
    analyze_video_emotion(video_path)
