import base64
import json
import os
import requests
import uuid
from dotenv import load_dotenv
from openai import OpenAI
from typing import List
from util import Summary
from util import LinkedProperty

load_dotenv()

open_ai_key: str = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=open_ai_key)


def create_function(properties: List[LinkedProperty]):
    entries = {}
    for prop in properties:
        entries[prop.property] = {
            "type": prop.type,
            "description": prop.description
        }

    return {
        "name": "page_summary",
        "description": "Compare the pages based off the users prompt.",
        "parameters": {
            "type": "object",
            "required": ["summary", "has_change"],
            "properties": entries
        }
    }


def download_image(url: str):
    file_name = f'{uuid.uuid4()}.png'
    file = open(os.path.join("screenshots", file_name), 'wb')
    response = requests.get(url)
    with file as f:
        f.write(response.content)
    return file.name


def encode_image(image_path: str):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def send_request(previous_image_data, current_image_data, query: str, properties: List[LinkedProperty]):
    functions = [create_function(properties)]
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


def query_chat_gpt(previous_snapshot_url: str,
                   current_snapshot_url: str,
                   chat_gpt_query: str,
                   properties: List[LinkedProperty]) -> Summary:
    encoded_previous_snapshot = encode_image(download_image(previous_snapshot_url))
    encoded_current_snapshot = encode_image(download_image(current_snapshot_url))
    response = send_request(encoded_previous_snapshot, encoded_current_snapshot, chat_gpt_query, properties)

    parsed_response = json.loads(response.choices[0].message.function_call.arguments)

    summary = Summary(**parsed_response)

    return summary
