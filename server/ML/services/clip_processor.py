import cv2
from collections import defaultdict, Counter
import os
import logging
import subprocess
from datetime import datetime, timedelta
import tempfile

class ClipProcessor:
    def __init__(self):
        self.logger = logging.getLogger('main')  # Use main logger since ClipProcessor is part of main processing
        self.current_clips = []  # List of (path, description, emotion) tuples for viral clips
        self.events_by_clip = defaultdict(list)
        self.emotions_by_clip = defaultdict(list)
        self.is_clip_viral = defaultdict(bool)
        self.hype_start_time = None  # Track when hype moments start
        self.in_hype_moment = False  # Track if we're currently in a hype moment
        self.hype_descriptions = []  # Store descriptions of what's happening during hype moments
        
    def add_event(self, clip_id: str, event: dict):
        """Add an event to a specific clip's timeline"""
        self.events_by_clip[clip_id].append(event)
        if event["type"] == "emotion":
            self.emotions_by_clip[clip_id].append(event["emotion"])
            self.logger.info(f"Added emotion {event['emotion']} to clip {clip_id}")
        
    def get_dominant_emotion(self, clip_id: str) -> tuple:
        """Get the most frequent non-neutral emotion and its frequency"""
        emotions = [e.lower() for e in self.emotions_by_clip[clip_id]]
        if not emotions:
            self.logger.info(f"No emotions found for clip {clip_id}")
            return ("neutral", 0)
            
        # Count emotions excluding neutral
        emotion_counts = Counter(e for e in emotions if e != "neutral")
        if not emotion_counts:
            self.logger.info(f"Only neutral emotions found for clip {clip_id}")
            return ("neutral", 0)
            
        # Get the most common emotion and its count
        dominant_emotion, count = emotion_counts.most_common(1)[0]
        self.logger.info(f"Clip {clip_id} dominant emotion: {dominant_emotion} ({count}/{len(emotions)})")
        return (dominant_emotion, count)
        
    def get_clip_description(self, clip_id: str) -> str:
        """Get the most relevant scene description for the clip"""
        scene_events = [e for e in self.events_by_clip[clip_id] if e["type"] == "scene"]
        if not scene_events:
            self.logger.info(f"No scene descriptions found for clip {clip_id}")
            return "Unknown scene"
        # Take the description from the middle of the clip for best representation
        middle_idx = len(scene_events) // 2
        description = scene_events[middle_idx].get("description", "Unknown scene")
        self.logger.info(f"Clip {clip_id} scene description: {description}")
        return description
        
    def start_hype_moment(self):
        """Called when chat activity indicates start of a hype moment"""
        if not self.in_hype_moment:
            self.in_hype_moment = True
            self.hype_start_time = datetime.now()
            self.logger.info(f"🔥 Starting hype moment at {self.hype_start_time}")

    def end_hype_moment(self):
        """Called when chat activity indicates end of hype moment"""
        if self.in_hype_moment:
            self.in_hype_moment = False
            self.logger.info("📉 Hype moment ended")

    def check_viral_status(self, clip_id: str, clip_path: str = None) -> tuple:
        """
        Only runs emotion/scene analysis if we're in a hype moment.
        Logs everything with the hype-start timestamp.
        Returns (is_viral, description, peak_time) as before.
        """
        logger = self.logger

        # If we’re not in a hype moment, skip analysis entirely
        if not self.in_hype_moment:
            logger.info(f"Clip {clip_id}: skipping, not in hype moment")
            return False, None, None

        # use the recorded hype-start as our “event timestamp”
        ts = self.hype_start_time or datetime.now()
        prefix = f"[{ts:%H:%M:%S}]"

        # gather emotions
        emotions = [e.lower() for e in self.emotions_by_clip[clip_id]]
        total = len(emotions)
        non_neutrals = Counter(e for e in emotions if e != "neutral")

        if total == 0 or not non_neutrals:
            logger.info(f"{prefix} Clip {clip_id}: no strong emotions → not viral")
            return False, None, None

        # pick dominant
        dominant, count = non_neutrals.most_common(1)[0]
        ratio = count / total

        # pick a representative scene
        scenes = [e for e in self.events_by_clip[clip_id] if e["type"] == "scene"]
        desc = scenes[len(scenes)//2]["description"] if scenes else "Unknown scene"

        # print with timestamp prefix
        print(f"{prefix} Clip {clip_id}:")
        print(f"{prefix}   - Emotion: {dominant} ({count}/{total} = {ratio:.2%})")
        print(f"{prefix}   - Scene: {desc}")

        is_viral = ratio >= 0.3
        peak_time = next(
            (e["video_time"] for e in self.events_by_clip[clip_id]
            if e["type"]=="emotion" and e["emotion"].lower()==dominant),
            0.0
        )

        if is_viral:
            logger.info(f"{prefix} 🎯 Clip {clip_id} marked VIRAL at peak {peak_time:.1f}s")
            # keep for concatenation if needed
            if clip_path:
                self.current_clips.append((clip_path, desc, dominant))
        else:
            logger.info(f"{prefix} ❌ Clip {clip_id} not viral (ratio {ratio:.2%})")

        return is_viral, desc, peak_time
        
    def concatenate_clips(self, output_path: str) -> bool:
        """
        Concatenate all viral clips in the current batch into one MP4,
        using ffmpeg concat demuxer with -c copy to avoid re-encoding.
        """
        if not self.current_clips:
            self.logger.info("[Processor] No viral clips to concatenate")
            return False

        # build a temporary file list for ffmpeg
        with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as f:
            for clip_path, _, _ in self.current_clips:
                f.write(f"file '{os.path.abspath(clip_path)}'\n")
            list_file = f.name

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat', '-safe', '0',
            '-i', list_file,
            '-c', 'copy',
            output_path
        ]

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"[Processor] FFmpeg concat failed: {e}")
            os.remove(list_file)
            return False
        finally:
            os.remove(list_file)

        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            self.logger.info(f"[Processor] ✅ Saved viral compilation to {output_path}")
            self.current_clips.clear()
            return True
        else:
            self.logger.error(f"[Processor] Output file not created or empty: {output_path}")
            self.current_clips.clear()
            return False