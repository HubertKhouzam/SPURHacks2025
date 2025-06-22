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
import logging
import socket
import subprocess
import tempfile
import shutil
from datetime import datetime
from collections import deque
import logging.handlers

import cv2
from deepface import DeepFace
from services.intern import process_video
from services.transcript import transcribe_video
from services.clip_processor import ClipProcessor


# ── Logging Setup ──────────────────────────────────────────────────────────────
def setup_logging(log_dir='logs'):
    os.makedirs(log_dir, exist_ok=True)
    loggers = {}
    for comp in ['main', 'emotion', 'chat', 'intern', 'transcript']:
        path = os.path.join(log_dir, f"{comp}.log")
        open(path, 'w').close()
        logger = logging.getLogger(comp)
        logger.setLevel(logging.INFO)
        fh = logging.handlers.RotatingFileHandler(path, maxBytes=1_000_000, backupCount=5)
        fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(fh)
        loggers[comp] = logger
    return loggers

loggers = setup_logging()
print("Loggers initialized")


# ── Helpers ────────────────────────────────────────────────────────────────────
# Removed get_clip_number function as it's no longer needed with timestamp-based filenames


def is_video_file_complete_and_valid(path: str, min_stability_time: float = 3.0) -> bool:
    """
    Check if video file is complete, stable, and not corrupted.
    Returns True only if:
    1. File exists and has content
    2. File size is stable for min_stability_time seconds
    3. OpenCV can open the file without errors
    4. File has expected video properties
    5. Can actually read frames without corruption
    """
    logger = loggers['main']
    
    try:
        # Check if file exists and has content
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            return False
            
        # Multiple stability checks with longer waits
        for check_round in range(3):  # Do 3 rounds of stability checking
            initial_size = os.path.getsize(path)
            time.sleep(min_stability_time)
            
            if not os.path.exists(path):  # File might have been deleted
                return False
                
            final_size = os.path.getsize(path)
            if initial_size != final_size:
                logger.debug(f"File {path} still growing (round {check_round+1}): {initial_size} -> {final_size}")
                return False
                
        # Additional stability check - wait longer for final validation
        time.sleep(1.0)
        
        # Test if OpenCV can open the file properly
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            logger.warning(f"OpenCV cannot open {path}")
            cap.release()
            return False
            
        # Check basic video properties
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Validate properties first
        if frame_count <= 0 or fps <= 0 or width <= 0 or height <= 0:
            logger.warning(f"Invalid video properties for {path}: frames={frame_count}, fps={fps}, size={width}x{height}")
            cap.release()
            return False
            
        # Try to read first few frames to ensure no corruption
        frames_to_test = min(10, frame_count)
        for i in range(frames_to_test):
            ret, frame = cap.read()
            if not ret or frame is None:
                logger.warning(f"Cannot read frame {i} from {path}")
                cap.release()
                return False
                
        cap.release()
        logger.debug(f"Video {path} validated: {frame_count} frames, {fps} fps, {width}x{height}")
        return True
        
    except Exception as e:
        logger.warning(f"Error validating video file {path}: {e}")
        return False


def create_safe_copy(source_path: str, temp_dir: str = None) -> str:
    """
    Create a safe copy of the video file to avoid corruption during processing.
    Returns path to the copied file.
    """
    if temp_dir is None:
        temp_dir = tempfile.gettempdir()
    
    os.makedirs(temp_dir, exist_ok=True)
    base_name = os.path.basename(source_path)
    safe_path = os.path.join(temp_dir, f"safe_{int(time.time())}_{base_name}")
    
    try:
        shutil.copy2(source_path, safe_path)
        return safe_path
    except Exception as e:
        loggers['main'].error(f"Failed to create safe copy of {source_path}: {e}")
        return source_path  # Fallback to original


def concatenate_two_clips(a, b, out_path):
    """
    Use ffmpeg concat demuxer (no re-encode) to stitch a + b into out_path.
    Added error handling and validation.
    """
    logger = loggers['main']
    
    # Validate input files first
    for clip_path in [a, b]:
        if not is_video_file_complete_and_valid(clip_path, min_stability_time=0.5):
            logger.error(f"Input clip {clip_path} is not valid for concatenation")
            return False
    
    with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as tf:
        tf.write(f"file '{os.path.abspath(a)}'\n")
        tf.write(f"file '{os.path.abspath(b)}'\n")
        list_file = tf.name

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    cmd = [
        'ffmpeg', '-y',
        '-f', 'concat', '-safe', '0',
        '-i', list_file,
        '-c', 'copy',
        '-avoid_negative_ts', 'make_zero',  # Handle timestamp issues
        out_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.debug(f"FFmpeg concat successful for {out_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg concat failed: {e}")
        if e.stderr:
            logger.error(f"FFmpeg stderr: {e.stderr}")
        os.remove(list_file)
        return False
    finally:
        if os.path.exists(list_file):
            os.remove(list_file)

    # Validate output
    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        if is_video_file_complete_and_valid(out_path, min_stability_time=0.1):
            logger.info(f"✅ Concatenated clip saved to {out_path}")
            return True
        else:
            logger.error(f"❌ Output file created but appears corrupted: {out_path}")
            return False
    else:
        logger.error(f"❌ Output file missing or empty: {out_path}")
        return False


# ── Workers ────────────────────────────────────────────────────────────────────
def emotion_worker(video_path, event_q: queue.Queue, sample_every=10):
    logger = loggers['emotion']
    
    # Wait for the original file to be completely ready first
    logger.info(f"Emotion worker waiting for file: {video_path}")
    if not wait_for_file_stability(video_path, max_wait=10.0):
        logger.error(f"Video file not ready for emotion analysis: {video_path}")
        return
    
    # Additional safety wait
    time.sleep(2.0)
    
    # Create safe copy for processing
    safe_path = create_safe_copy(video_path, temp_dir='temp_processing')
    
    try:
        # Validate the safe copy too
        if not is_video_file_complete_and_valid(safe_path, min_stability_time=0.5):
            logger.error(f"Safe copy is corrupted: {safe_path}")
            return
            
        cap = cv2.VideoCapture(safe_path)
        if not cap.isOpened():
            logger.error(f"Cannot open video file: {safe_path}")
            return
            
        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 1
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        idx = 0
        logger.info(f"Emotion worker started (FPS={fps}, frames={total_frames}) for {video_path}")

        while cap.isOpened() and idx < total_frames:
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
    
    for t in threads:
        t.start()

    start = time.time()
    while time.time() - start < 6.0 and any(t.is_alive() for t in threads):
        try:
            evt = events.get(timeout=0.1)
            processor.add_event(clip_id, evt)
        except queue.Empty:
            continue

    # Wait a bit longer for threads to finish gracefully
    for t in threads:
        t.join(timeout=1.0)

    is_viral, desc, peak = processor.check_viral_status(clip_id, path)
    return is_viral, desc, peak


def wait_for_file_stability(path: str, max_wait: float = 15.0) -> bool:
    """
    Wait for a file to become stable and ready for processing.
    Uses aggressive checking with multiple validation passes.
    Returns True if file is ready, False if timeout or file issues.
    """
    logger = loggers['main']
    start_time = time.time()
    check_interval = 0.5
    
    logger.info(f"Waiting for file stability: {os.path.basename(path)}")
    
    while time.time() - start_time < max_wait:
        # First check if file exists and has minimum size
        if not os.path.exists(path):
            time.sleep(check_interval)
            continue
            
        file_size = os.path.getsize(path)
        if file_size < 1000:  # Files should be at least 1KB for 6-second clips
            logger.debug(f"File {path} too small: {file_size} bytes")
            time.sleep(check_interval)
            continue
        
        # Wait a bit more after file appears to have content
        time.sleep(2.0)
        
        # Now do the full validation with frame reading
        if is_video_file_complete_and_valid(path, min_stability_time=1.0):
            logger.info(f"File {path} is stable and ready (took {time.time() - start_time:.1f}s)")
            return True
            
        time.sleep(check_interval)
    
    logger.warning(f"File {path} did not become stable within {max_wait}s")
    return False


# ── Main Loop ─────────────────────────────────────────────────────────────────
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Viral Clip Detector')
    parser.add_argument('--clips_dir', default='clips', help='Directory containing 6s mp4 snippets')
    args = parser.parse_args()
    run(args.clips_dir)