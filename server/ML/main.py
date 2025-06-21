"""
main.py
Run with:  python main.py --video output2.mp4

Requires:
  pip install deepface opencv-python pyenv-installed Python 3.9+
"""
import argparse
import queue
import threading
import time
from datetime import datetime, timedelta
import socket
from collections import deque, Counter

from deepface import DeepFace
import cv2


###############################################################################
# ---------------------------  Emotion Worker  --------------------------------
###############################################################################
def emotion_worker(video_path: str, event_q: queue.Queue, sample_every=10):
    cap = cv2.VideoCapture(video_path if video_path else 0)  # 0 == webcam
    frame_idx = 0
    print("[Emotion] Worker started")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % sample_every == 0:
            try:
                res = DeepFace.analyze(
                    frame,
                    actions=["emotion"],
                    enforce_detection=False,
                )
                dominant = res[0]["dominant_emotion"]
                if dominant.lower() != "neutral":
                    event_q.put(
                        {
                            "type": "emotion",
                            "timestamp": datetime.now(),
                            "emotion": dominant,
                        }
                    )
            except Exception:
                pass  # ignore frames with no face / bad detection

        frame_idx += 1

    cap.release()
    print("[Emotion] Worker finished")


###############################################################################
# -----------------------------  Chat Worker  ---------------------------------
###############################################################################
def chat_worker(event_q: queue.Queue):
    # Twitch IRC connection info
    HOST, PORT = "irc.chat.twitch.tv", 6667
    NICK = "flaccdo"
    TOKEN = "oauth:5hat2rxorg0y8j0ti7gt13rdtztadj"
    CHANNEL = "#jasontheween"

    # Detection config
    WINDOW_SECONDS = 60
    PEAK_MULTIPLIER = 2
    PRE_ROLL = 10
    END_COOLDOWN = 10
    ALPHA = 0.1  # EMA

    message_times = deque()
    baseline_rate = 0.5
    in_peak = False
    last_peak_time = None
    clip_start = None

    sock = socket.socket()
    sock.connect((HOST, PORT))
    sock.send(f"PASS {TOKEN}\n".encode())
    sock.send(f"NICK {NICK}\n".encode())
    sock.send(f"JOIN {CHANNEL}\n".encode())
    print(f"[Chat] Connected to {CHANNEL} as {NICK}")

    while True:
        resp = sock.recv(2048).decode(errors="ignore")

        for line in resp.strip().split("\r\n"):
            if line.startswith("PING"):
                sock.send("PONG :tmi.twitch.tv\n".encode())
                continue

            if "PRIVMSG" in line:
                now = datetime.now()
                message_times.append(now)

                # window maintenance
                while (
                    len(message_times) >= 2
                    and (message_times[-1] - message_times[0]).total_seconds()
                    > WINDOW_SECONDS
                ):
                    message_times.popleft()

                duration = (message_times[-1] - message_times[0]).total_seconds()
                rate = len(message_times) / duration if duration else 0
                baseline_rate = (1 - ALPHA) * baseline_rate + ALPHA * rate

                # hype detection
                if not in_peak and rate > PEAK_MULTIPLIER * baseline_rate:
                    in_peak = True
                    last_peak_time = now
                    clip_start = now - timedelta(seconds=PRE_ROLL)
                    print(f"[Chat] 🔥 HYPE start {clip_start.strftime('%H:%M:%S')}")

                elif in_peak:
                    if rate < baseline_rate * 1.1:
                        if (now - last_peak_time).total_seconds() >= END_COOLDOWN:
                            in_peak = False
                            clip_end = now
                            event_q.put(
                                {
                                    "type": "hype",
                                    "start": clip_start,
                                    "end": clip_end,
                                }
                            )
                            print(
                                f"[Chat] 🎬 HYPE end   {clip_end.strftime('%H:%M:%S')}"
                            )


###############################################################################
# -----------------------------  Main Runner  ---------------------------------
###############################################################################
def run(video_path: str):
    events = queue.Queue()

    # spawn workers
    t1 = threading.Thread(
        target=emotion_worker, args=(video_path, events), daemon=True
    )
    t2 = threading.Thread(target=chat_worker, args=(events,), daemon=True)
    t1.start()
    t2.start()

    # central event pump
    print("[Main] Listening for hype & emotions (Ctrl-C to quit)…")
    try:
        while True:
            evt = events.get()
            if evt["type"] == "emotion":
                ts = evt["timestamp"].strftime("%H:%M:%S")
                print(f"[Event] 😃 Non-neutral emotion '{evt['emotion']}' at {ts}")
            elif evt["type"] == "hype":
                s, e = evt["start"].strftime("%H:%M:%S"), evt["end"].strftime("%H:%M:%S")
                print(f"[Event] 🚀 Hype window {s} → {e}")
    except KeyboardInterrupt:
        print("\n[Main] Shutting down…")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hype + Emotion listener")
    parser.add_argument(
        "--video",
        default="output2.mp4",
        help="Path to video file (or leave empty for webcam)",
    )
    run(**vars(parser.parse_args()))
