from openai import OpenAI
import base64

def call_intern_api():
    client = OpenAI(
        api_key="eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiI4MjYwMzExMSIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc1MDU0NDU2OCwiY2xpZW50SWQiOiJlYm1ydm9kNnlvMG5semFlazF5cCIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiMWZmZjRhZmUtYTVjZS00ODQ4LWE5OWItY2RhZTIyYmYwNDMwIiwiZW1haWwiOiIiLCJleHAiOjE3NjYwOTY1Njh9.FQ5ifmAytwX1yGaZuUI8So-1qUMNaXC82Yi3_fun4r6dQB8BfpZ7v4Dj1wha9q8Dw5_R9-CBSrCu4sKYfC3gog",  # Token is passed here without 'Bearer'
        base_url="https://chat.intern-ai.org.cn/api/v1/",
    )


    with open("/Users/eddiechen/Developer/SPURHacks2025/server/ML/images/jason.png", "rb") as img_file:
        img_base64 = base64.b64encode(img_file.read()).decode("utf-8")
    img_data_url = f"data:image/png;base64,{img_base64}"

    chat_rsp = client.chat.completions.create(
        model="internvl2.5-latest",
        messages=[
            {"role": "user", "content": [
                {"type": "text", "text": "whats in the image. keep to very short answer. Exclude details. Focus on the people and their actions."},
                {"type": "image_url", "image_url": {"url": img_data_url}}
            ]}
        ],
    )

    for choice in chat_rsp.choices:
        print(choice.message.content)

if __name__ == "__main__":
    call_intern_api()
