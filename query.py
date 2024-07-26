import base64
import json
import os
import requests
import uuid
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()

open_ai_key: str = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=open_ai_key)


class Summary(BaseModel):
    has_change: bool
    summary: str


functions = [
    {
        "name": "page_summary",
        "description": "Compare the pages based off the users prompt.",
        "parameters": {
            "type": "object",
            "required": ["summary", "has_change"],
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Summary of the changes between snapshots."
                },
                "has_change": {
                    "type": "boolean",
                    "description": "Snapshots are noticeably different."
                },
            }
        }
    }
]


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
    return client.chat.completions.create(
        messages=
        [{
            "role": "user",
            "content": [{"type": "text", "text": "Answer the following query about the webpage snapshots: " + query +
                                                 ". Give the response in the format of page_summary function call."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{previous_image_data}"}},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{current_image_data}"}}]
        }],
        model="gpt-4-turbo",
        functions=functions,
        function_call={
            "name": functions[0]["name"]
        },
        temperature=0,
        max_tokens=300
    )


def query_chat_gpt(previous_snapshot_url: str, current_snapshot_url: str, chat_gpt_query: str) -> str:
    encoded_previous_snapshot = encode_image(download_image(previous_snapshot_url))
    encoded_current_snapshot = encode_image(download_image(current_snapshot_url))
    response = send_request(encoded_previous_snapshot, encoded_current_snapshot, chat_gpt_query)

    parsed_response = json.loads(response.choices[0].message.function_call.arguments)

    print("parsed_response", parsed_response)

    summary = Summary(**parsed_response)

    return summary.summary
