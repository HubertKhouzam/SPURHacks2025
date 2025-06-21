from deepface import DeepFace
import cv2

def analyze_video_emotion(video_path):
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    emotions = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % 5 == 0:  # sample every 5th frame
            try:
                result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
                emotions.append(result[0]['dominant_emotion'])
            except:
                pass

        frame_count += 1

    cap.release()

    from collections import Counter
    print(Counter(emotions).most_common())
