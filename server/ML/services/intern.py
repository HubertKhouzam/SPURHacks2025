from openai import OpenAI
import base64
import cv2
import time
import logging
from datetime import datetime, timedelta

def process_video(video_path: str, event_q=None):
    logger = logging.getLogger('intern')
    client = OpenAI(
        base_url="https://chat.intern-ai.org.cn/api/v1/",
        api_key="eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiI4MjYwMzExMSIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc1MDU0NDU2OCwiY2xpZW50SWQiOiJlYm1ydm9kNnlvMG5semFlazF5cCIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiMWZmZjRhZmUtYTVjZS00ODQ4LWE5OWItY2RhZTIyYmYwNDMwIiwiZW1haWwiOiIiLCJleHAiOjE3NjYwOTY1Njh9.Y3LDmxXwPTDctag9sjrq281gxdTDoyfaLZVbFnXSi72mKmPQ4b5VfFDMD48RuDhkFsYRFyMR5PgQCDE7EuANvA"
    )

    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_count = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        # Process one frame per second
        if frame_count % fps == 0:
            # Convert frame to base64
            _, buffer = cv2.imencode('.jpg', frame)
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            img_data_url = f"data:image/jpeg;base64,{img_base64}"
            
            # Get timestamp
            current_second = frame_count // fps
            timestamp = str(timedelta(seconds=current_second))
            
            try:
                chat_rsp = client.chat.completions.create(
                    model="internvl2.5-latest",
                    messages=[
                        {"role": "user", "content": [
                            {"type": "text", "text": "这张照片上发生了什么？请用英语说出来，字数控制在10个字以内。"},
                            {"type": "image_url", "image_url": {"url": img_data_url}}
                        ]}
                    ],
                )
                
                description = chat_rsp.choices[0].message.content
                if event_q:
                    event_q.put({
                        "type": "scene",
                        "timestamp": datetime.now(),
                        "description": description,
                        "frame": current_second
                    })
                else:
                    logger.info(f"Timestamp: {timestamp}")
                    logger.info(f"Frame {current_second}: {description}")
                
            except Exception as e:
                logger.error(f"Error processing frame at {timestamp}: {str(e)}")
            
            # Add a small delay to avoid rate limiting
            time.sleep(0.5)
            
        frame_count += 1
    
    cap.release()

if __name__ == "__main__":
    # Set up basic logging for standalone usage
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    video_path = "videos/IMG_2227.mp4" 
    process_video(video_path)