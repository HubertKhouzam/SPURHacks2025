"""
main.py
Run with:  python main.py --clips_dir clips/

Requires:
  pip install deepface opencv-python openai-whisper pyenv-installed Python 3.9+
"""
import argparse
import queue
import threading
import time
from datetime import datetime, timedelta
import socket
from collections import deque, Counter
import os
import glob

from deepface import DeepFace
import cv2
from services.intern import process_video
from services.transcript import transcribe_video
from services.clip_processor import ClipProcessor



###############################################################################
# ---------------------------  Emotion Worker  --------------------------------
###############################################################################
def emotion_worker(video_path: str, event_q: queue.Queue, sample_every=10):
    cap = cv2.VideoCapture(video_path if video_path else 0)  # 0 == webcam
    frame_idx = 0
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    print(f"[Emotion] Worker started - FPS: {fps}")

    try:
        while cap.isOpened():
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
                    video_time = frame_idx / fps  # Calculate timestamp in video
                    if dominant.lower() != "neutral":
                        event_q.put(
                            {
                                "type": "emotion",
                                "timestamp": datetime.now(),
                                "video_time": video_time,
                                "emotion": dominant,
                            }
                        )
                except Exception as e:
                    print(f"[Emotion] Frame {frame_idx} analysis error: {str(e)}")
                    pass

            frame_idx += 1
            
    except Exception as e:
        print(f"[Emotion] Worker error: {str(e)}")
    finally:
        cap.release()

    cap.release()
    print("[Emotion] Worker finished")


###############################################################################
# -----------------------------  Chat Worker  ---------------------------------
###############################################################################
def chat_worker(event_q: queue.Queue, hype_detected: threading.Event = None):
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
                    if hype_detected:
                        hype_detected.set()  # Signal that hype was detected

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
# -----------------------------  Intern Worker  ---------------------------------
###############################################################################
def intern_worker(video_path: str, event_q: queue.Queue):
    print("[Intern] Worker started")
    try:
        process_video(video_path)
    except Exception as e:
        print(f"[Intern] Error: {str(e)}")
    finally:
        print("[Intern] Worker finished")

###############################################################################
# -----------------------------  Transcript Worker  -----------------------------
###############################################################################
def transcript_worker(video_path: str, event_q: queue.Queue):
    print("[Transcript] Worker started")
    try:
        transcribe_video(video_path, event_q)
    except Exception as e:
        print(f"[Transcript] Error: {str(e)}")
    finally:
        print("[Transcript] Worker finished")

###############################################################################
# -----------------------------  Main Runner  ---------------------------------
###############################################################################
def process_single_clip(clip_path: str, processor: ClipProcessor, clip_id: str):
    """Process a single clip and collect its events. Analyze emotions to determine virality."""
    events = queue.Queue()
    print(f"[Main] Processing clip: {clip_path}")
    
    # Start all workers in parallel
    workers = [
        threading.Thread(target=emotion_worker, args=(clip_path, events), daemon=True),
        threading.Thread(target=intern_worker, args=(clip_path, events), daemon=True),
        threading.Thread(target=transcript_worker, args=(clip_path, events), daemon=True),
        threading.Thread(target=chat_worker, args=(events,), daemon=True)
    ]
    
    for worker in workers:
        worker.start()
    
    try:
        # Process events with timeout
        start_time = time.time()
        while any(t.is_alive() for t in workers):
            if time.time() - start_time > 6.0:  # Match clip length (6 seconds)
                print(f"[Main] Finished processing clip: {clip_path}")
                break
            try:
                evt = events.get(timeout=0.1)  # Shorter timeout for faster processing
                processor.add_event(clip_id, evt)
                
                # Print event
                if evt["type"] == "emotion":
                    ts = evt["timestamp"].strftime("%H:%M:%S")
                    print(f"[Event] 😃 Emotion: '{evt['emotion']}' at {ts}")
                elif evt["type"] == "scene":
                    ts = evt["timestamp"].strftime("%H:%M:%S")
                    print(f"[Event] 🎥 Frame {evt['frame']}: {evt['description']}")
                elif evt["type"] == "transcript":
                    print(f"[Event] 💬 {evt['video_timestamp']}s: {evt['text']}")
            except queue.Empty:
                continue
                
    except KeyboardInterrupt:
        print("\n[Main] Shutting down...")
    
    # Get dominant emotion and determine if viral
    dominant_emotion, count = processor.get_dominant_emotion(clip_id)
    if dominant_emotion == "neutral":
        print(f"[Main] 😐 Clip {clip_id} is mostly neutral, skipping...")
        return False
        
    print(f"[Main] 🎭 Dominant emotion in {clip_id}: {dominant_emotion}")
    is_viral = processor.check_viral_status(clip_id)
    return is_viral

def run(clips_dir: str):
    processor = ClipProcessor()
    processed_files = set()
    initial_hype_ignored = False
    
    print(f"[Main] Monitoring directory: {clips_dir}")
    
    try:
        while True:
            # Check for new clips
            clips = sorted(glob.glob(os.path.join(clips_dir, "*.mp4")))  # Sort to process in order
            new_clips = [c for c in clips if c not in processed_files]
            
            if not initial_hype_ignored and new_clips:
                print("[Main] Ignoring initial hype moment...")
                initial_hype_ignored = True
                processed_files.add(new_clips[0])
                new_clips = new_clips[1:]
            
            for clip_path in new_clips:
                clip_id = os.path.basename(clip_path)
                is_viral = process_single_clip(clip_path, processor, clip_id)
                
                is_viral, description, peak_time = processor.check_viral_status(clip_id)
                if is_viral:
                    full_path = os.path.abspath(clip_path)
                    print(f"\n[Main] 🎯 Viral clip detected: {clip_id}")
                    print(f"[Main] 🎬 Trigger: {description}")
                    print(f"[Main] ⏱️ Peak moment: {peak_time:.1f}s")
                    processor.current_clips.append((full_path, description, peak_time))
                else:
                    print(f"[Main] Regular clip: {clip_id}")
                    # If we have viral clips and hit a non-viral one, concatenate
                    if processor.current_clips:
                        compilation_dir = os.path.join(os.path.dirname(clips_dir), "compilations")
                        os.makedirs(compilation_dir, exist_ok=True)
                        output_path = os.path.join(compilation_dir, f"viral_compilation_{int(time.time())}.mp4")
                        result = processor.concatenate_clips(output_path)
                        if result:
                            print(f"[Main] 🎬 Created viral compilation: {output_path}")
                        processor.current_clips = []  # Reset for next batch
                        
                processed_files.add(clip_path)
            
            # Sleep before checking for new files
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[Main] Shutting down...")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Viral Clip Detector")
    parser.add_argument(
        "--clips_dir",
        default="clips",
        help="Directory containing input clips",
    )
    args = parser.parse_args()
    run(args.clips_dir)
