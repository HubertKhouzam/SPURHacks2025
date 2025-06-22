#!/usr/bin/env python3
"""
main.py - Fixed version with video corruption protection
Run with:  python main.py --clips_dir clips/

Requires:
  pip install deepface opencv-python openai-whisper pyenv-installed Python 3.9+
"""
import argparse
import queue
import threading
import time
import os
import glob

from deepface import DeepFace
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
            if not ret or frame is None:
                logger.debug(f"End of video or invalid frame at {idx}")
                break
                
            if idx % sample_every == 0:
                try:
                    res = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
                    dom = res[0]['dominant_emotion']
                    if dom.lower() != 'neutral':
                        event_q.put({
                            'type': 'emotion',
                            'timestamp': datetime.now(),
                            'video_time': idx / fps,
                            'emotion': dom
                        })
                        logger.debug(f"Detected {dom} at {idx/fps:.1f}s")
                except Exception as e:
                    logger.error(f"Frame {idx} emotion analysis error: {e}")
            idx += 1

        cap.release()
        logger.info(f"Emotion worker finished - processed {idx} frames")
        
    except Exception as e:
        logger.error(f"Emotion worker failed: {e}")
    finally:
        # Clean up safe copy
        if safe_path != video_path and os.path.exists(safe_path):
            try:
                os.remove(safe_path)
                logger.debug(f"Cleaned up safe copy: {safe_path}")
            except Exception as e:
                logger.warning(f"Could not remove safe copy {safe_path}: {e}")


def chat_worker(_unused_q, processor: ClipProcessor):
    logger = loggers['chat']
    HOST, PORT = "irc.chat.twitch.tv", 6667
    NICK = "flaccdo"
    TOKEN = "oauth:5hat2rxorg0y8j0ti7gt13rdtztadj"
    CHANNEL = "#kvinhe"

    WINDOW, THRESH, COOLDOWN = 20, 10, 10
    
    try:
        sock = socket.socket()
        sock.settimeout(30)  # Add timeout to prevent hanging
        sock.connect((HOST, PORT))
        sock.send(f"PASS {TOKEN}\r\n".encode())
        sock.send(f"NICK {NICK}\r\n".encode())
        sock.send(f"JOIN {CHANNEL}\r\n".encode())
        logger.info(f"Connected to {CHANNEL}")
    except Exception as e:
        logger.error(f"Failed to connect to Twitch IRC: {e}")
        return

    times = deque()
    in_peak = False
    last_peak = None

    try:
        while True:
            data = sock.recv(2048).decode(errors='ignore')
            for line in data.split('\r\n'):
                if line.startswith('PING'):
                    sock.send('PONG :tmi.twitch.tv\r\n'.encode())
                    continue
                if 'PRIVMSG' not in line:
                    continue

                msg = line.split('PRIVMSG',1)[1].split(':',1)[1].strip()
                now = datetime.now()
                print(f"[{now:%H:%M:%S}] {msg}", flush=True)

                times.append(now)
                while times and (now - times[0]).total_seconds() > WINDOW:
                    times.popleft()
                count = len(times)

                if not in_peak and count > THRESH:
                    in_peak = True
                    last_peak = now
                    processor.start_hype_moment()
                    
                    # Start intern analysis of current clips
                    clips = glob.glob(os.path.join('clips', '*.mp4'))
                    if clips:
                        latest_clip = max(clips, key=os.path.getmtime)
                        try:
                            # Process latest clip with intern to understand what's happening
                            logger.info(f"Analyzing hype moment in {os.path.basename(latest_clip)}")
                            description = process_video(latest_clip)
                            if description:
                                logger.info(f"🎥 Hype context: {description}")
                                print(f"🎥 {description}", flush=True)
                        except Exception as e:
                            logger.error(f"Failed to analyze hype clip: {e}")
                    
                    logger.info(f"🔥 HYPE start {now:%H:%M:%S}")
                    print(f"🔥 HYPE START at {now:%H:%M:%S} 🔥", flush=True)

                if in_peak and count < THRESH and (now - last_peak).total_seconds() >= COOLDOWN:
                    in_peak = False
                    processor.end_hype_moment()
                    logger.info(f"📉 HYPE end {now:%H:%M:%S}")
                    print(f"📉 HYPE END at {now:%H:%M:%S} 📉", flush=True)
                    
    except Exception as e:
        logger.error(f"Chat worker error: {e}")
    finally:
        try:
            sock.close()
        except:
            pass


def intern_worker(video_path, event_q: queue.Queue):
    logger = loggers['intern']
    logger.info(f"Intern worker waiting for file: {video_path}")
    
    # Wait for file to be ready before processing
    if not wait_for_file_stability(video_path, max_wait=10.0):
        logger.warning(f"Video file not ready for intern processing: {video_path}")
        return
    
    # Additional safety wait
    time.sleep(1.0)
        
    try:
        logger.info("Intern worker started processing")
        process_video(video_path)
        logger.info("Intern worker finished successfully")
    except Exception as e:
        logger.error(f"Intern error: {e}")


def transcript_worker(video_path, event_q: queue.Queue):
    logger = loggers['transcript']
    logger.info(f"Transcript worker waiting for file: {video_path}")
    
    # Wait for file to be ready before processing
    if not wait_for_file_stability(video_path, max_wait=10.0):
        logger.warning(f"Video file not ready for transcript processing: {video_path}")
        return
    
    # Additional safety wait
    time.sleep(1.0)
        
    try:
        logger.info("Transcript worker started processing")
        transcribe_video(video_path, event_q)
        logger.info("Transcript worker finished successfully")
    except Exception as e:
        logger.error(f"Transcript error: {e}")


# ── Clip Processing ────────────────────────────────────────────────────────────
def process_single_clip(path, processor: ClipProcessor, clip_id: str):
    logger = loggers['main']
    
    # First validate the clip before processing
    if not is_video_file_complete_and_valid(path):
        logger.warning(f"Skipping invalid/incomplete clip: {clip_id}")
        return False, None, None
    
    events = queue.Queue()
    logger.info(f"Processing {clip_id}")

    threads = [
        threading.Thread(target=emotion_worker,  args=(path, events), daemon=True),
        threading.Thread(target=intern_worker,   args=(path, events), daemon=True),
        threading.Thread(target=transcript_worker,args=(path, events), daemon=True),
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
    logger = loggers['main']
    processor = ClipProcessor()
    processed = {}
    prev_clip = None

    # Create temp directory for safe copies
    os.makedirs('temp_processing', exist_ok=True)
    
    # start one global chat thread
    chat_thread = threading.Thread(target=chat_worker, args=(None, processor), daemon=True)
    chat_thread.start()

    os.makedirs('output', exist_ok=True)
    logger.info(f"Monitoring directory: {clips_dir}")

    while True:
        try:
            # Get all clips and sort by creation time (newest first)
            snippets = glob.glob(os.path.join(clips_dir, '*.mp4'))
            snippets.sort(key=os.path.getctime, reverse=True)

            # Process any new clips we haven't seen before
            new = [s for s in snippets if s not in processed]
            for clip in new:
                clip_id = os.path.basename(clip)
                logger.info(f"Found new clip: {clip_id}")
                
                # Wait for file to be stable before processing
                if not wait_for_file_stability(clip, max_wait=20.0):
                    logger.warning(f"Skipping unstable file: {clip_id}")
                    processed[clip] = time.time()  # Mark as processed
                    continue
                
                # Extra safety sleep after validation
                logger.info(f"File stable, waiting 3 more seconds before processing: {clip_id}")
                time.sleep(3.0)
                
                is_viral, desc, peak_time = process_single_clip(clip, processor, clip_id)

                if is_viral and prev_clip:
                    # Ensure previous clip is also stable before concatenation
                    logger.info(f"Viral clip detected! Checking previous clip stability...")
                    if wait_for_file_stability(prev_clip, max_wait=5.0):
                        # Double-check both files are ready for concatenation
                        time.sleep(2.0)  # Extra safety buffer
                        out = os.path.join('output', f"hype_{int(time.time())}.mp4")
                        logger.info(f"Concatenating {os.path.basename(prev_clip)} + {clip_id}")
                        if concatenate_two_clips(prev_clip, clip, out):
                            logger.info(f"🎬 Created 12s hype clip: {out}")
                            logger.info(f"🎯 Viral clip {clip_id} @ {peak_time:.1f}s: {desc}")
                            # Process the concatenated clip
                            try:
                                # Wait for output file to be stable too
                                if wait_for_file_stability(out, max_wait=5.0):
                                    process_video(out)
                                else:
                                    logger.error(f"Output file not stable: {out}")
                            except Exception as e:
                                logger.error(f"Error processing concatenated clip: {e}")
                        else:
                            logger.error("Failed to concatenate hype clip")
                    else:
                        logger.warning(f"Previous clip {prev_clip} not stable for concatenation")

                processed[clip] = os.path.getmtime(clip)
                prev_clip = clip

        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            
        time.sleep(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Viral Clip Detector")
    parser.add_argument(
        "--clips_dir",
        default="clips",
        help="Directory containing input clips",
    )
    args = parser.parse_args()
    run(args.clips_dir)