import cv2
from collections import defaultdict, Counter
import os
from datetime import datetime, timedelta

class ClipProcessor:
    def __init__(self):
        self.current_clips = []  # List of viral clips to concatenate
        self.events_by_clip = defaultdict(list)
        self.emotions_by_clip = defaultdict(list)
        self.is_clip_viral = defaultdict(bool)
        
    def add_event(self, clip_id: str, event: dict):
        """Add an event to a specific clip's timeline"""
        self.events_by_clip[clip_id].append(event)
        if event["type"] == "emotion":
            self.emotions_by_clip[clip_id].append(event["emotion"])
        
    def get_dominant_emotion(self, clip_id: str) -> tuple:
        """Get the most frequent non-neutral emotion and its frequency"""
        emotions = [e.lower() for e in self.emotions_by_clip[clip_id]]
        if not emotions:
            return ("neutral", 0)
            
        # Count emotions excluding neutral
        emotion_counts = Counter(e for e in emotions if e != "neutral")
        if not emotion_counts:
            return ("neutral", 0)
            
        # Get the most common emotion and its count
        dominant_emotion, count = emotion_counts.most_common(1)[0]
        return (dominant_emotion, count)
        
    def get_clip_description(self, clip_id: str) -> str:
        """Get the most relevant scene description for the clip"""
        scene_events = [e for e in self.events_by_clip[clip_id] if e["type"] == "scene"]
        if not scene_events:
            return "Unknown scene"
        # Take the description from the middle of the clip for best representation
        middle_idx = len(scene_events) // 2
        return scene_events[middle_idx].get("description", "Unknown scene")
        
    def check_viral_status(self, clip_id: str) -> tuple:
        """
        Check if a clip is viral based on:
        - Must have a dominant non-neutral emotion
        Returns: (is_viral: bool, description: str, timestamp: float)
        """
        dominant_emotion, count = self.get_dominant_emotion(clip_id)
        scene_description = self.get_clip_description(clip_id)
        
        if dominant_emotion == "neutral":
            print(f"[Processor] Clip {clip_id} is mostly neutral, skipping...")
            return False, None, None
            
        emotion_events = [e for e in self.events_by_clip[clip_id] if e["type"] == "emotion"]
        total_emotions = len(emotion_events)
        
        if total_emotions == 0:
            print(f"[Processor] No emotions detected in clip {clip_id}")
            return False, None, None
            
        emotion_ratio = count / total_emotions
        
        # Get the timestamp of the strongest emotion moment
        emotion_times = [e.get("video_time", 0) for e in emotion_events if e["emotion"].lower() == dominant_emotion.lower()]
        peak_time = emotion_times[len(emotion_times)//2] if emotion_times else 0
        
        print(f"[Processor] Clip {clip_id}:")
        print(f"  - Emotion: {dominant_emotion} ({count}/{total_emotions} = {emotion_ratio:.2%})")
        print(f"  - Scene: {scene_description}")
        print(f"  - Peak Time: {peak_time:.1f}s")
        
        # Consider viral if the dominant emotion appears in at least 30% of frames
        is_viral = emotion_ratio >= 0.3
        return is_viral, scene_description, peak_time
        
    def concatenate_clips(self, output_path: str):
        """Concatenate all viral clips in the current batch"""
        if not self.current_clips:
            print("[Processor] No clips to concatenate")
            return None
            
        print(f"[Processor] Concatenating {len(self.current_clips)} clips: {self.current_clips}")
            
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
        # Get the first clip to determine video properties
        cap = cv2.VideoCapture(self.current_clips[0])
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        
        # Create video writer with H.264 codec
        fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H.264 codec
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # Write each clip
        for clip_path in self.current_clips:
            cap = cv2.VideoCapture(clip_path)
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                out.write(frame)
            cap.release()
            
        out.release()
        return output_path
