from dotenv import load_dotenv
from openai import OpenAI
import base64
import os
import requests
import uuid

load_dotenv()

open_ai_key: str = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=open_ai_key)


def download_image(url):
    file_name = f'{uuid.uuid4()}.png'
    file = open(os.path.join("screenshots", file_name), 'wb')
    response = requests.get(url)
    with file as f:
        f.write(response.content)
    return file.name


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def send_request(previous_image_data, current_image_data, query):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {open_ai_key}"}
    payload = {
        "model": "gpt-4o",
        "messages": [{
            "role": "user",
            "content": [{"type": "text", "text": query},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{previous_image_data}"}},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{current_image_data}"}}]
        }],
        "max_tokens": 300
    }
    return requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload).json()


def query_chat_gpt(previous_snapshot_url: str, current_snapshot_url: str, chat_gpt_query: str) -> str:
    encoded_previous_snapshot = encode_image(download_image(previous_snapshot_url))
    encoded_current_snapshot = encode_image(download_image(current_snapshot_url))
    response = send_request(encoded_previous_snapshot, encoded_current_snapshot, chat_gpt_query)
    return response["choices"][0]["message"]["content"]
