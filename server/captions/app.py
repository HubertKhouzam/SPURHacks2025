import whisperx
import os
import subprocess

# Step 1: Transcribe video
input_video = "videoplayback.mp4"
srt_file = "captions.srt"
output_video = "videoplayback_captioned.mp4"

print("🔁 Transcribing with WhisperX...")
model = whisperx.load_model("large-v3", device="cuda")
result = model.transcribe(input_video)

print("📝 Writing SRT file...")
whisperx.utils.write_srt(result["segments"], srt_file)

# Step 2: Burn SRT into video using ffmpeg
print("🎬 Burning subtitles into video with FFmpeg...")
ffmpeg_command = [
    "ffmpeg",
    "-i", input_video,
    "-vf", f"subtitles={srt_file}",
    "-c:a", "copy",
    output_video
]

subprocess.run(ffmpeg_command, check=True)

# Step 3: Replace the original video with captioned version
print("🔄 Replacing original video...")
os.remove(input_video)
os.rename(output_video, input_video)

print("✅ Done! Original video replaced with captioned version.")
