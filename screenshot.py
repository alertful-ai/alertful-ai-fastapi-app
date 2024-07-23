import asyncio
import uuid
from typing import Dict, Set

from dotenv import load_dotenv
import os
from pyppeteer import launch
from supabase import create_client, Client
import boto3

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
aws_access_key_id: str = os.environ.get("AWS_ACCESS_KEY_ID")
aws_secret_access_key: str = os.environ.get("AWS_SECRET_ACCESS_KEY")
aws_endpoint_url: str = os.environ.get("AWS_ENDPOINT_URL")
aws_region: str = os.environ.get("AWS_REGION")
image_url: str = os.environ.get("IMAGE_URL")
BUCKET_NAME: str = os.environ.get("SUPABASE_BUCKET_NAME")
supabase: Client = create_client(url, key)

s3 = boto3.client(
    's3',
    region_name=aws_region,
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    endpoint_url=aws_endpoint_url
)


# Capture a screenshot of a URL and return the screenshot
async def capture_screenshot(page, page_url, file_path):
    await page.goto(page_url)
    await page.screenshot({'path': file_path, 'fullPage': True})


async def upload_to_supabase(file_name: str, file_path: str):
    try:
        s3.upload_file(file_path, BUCKET_NAME, file_name, ExtraArgs={'ContentType': 'image/png'})
        file_url = f"{image_url}/{file_name}"
        return file_url
    except Exception as e:
        print(f"Error uploading file: {e}")


async def process_page(page_url: str, browser) -> Dict[str, str]:
    page = await browser.newPage()
    await page.setViewport({'width': 1200, 'height': 800})

    file_name = f'{uuid.uuid4()}.png'
    local_file_path = f'screenshots/{file_name}'

    await capture_screenshot(page, page_url, local_file_path)
    img_url = await upload_to_supabase(file_name, local_file_path)

    await page.close()
    return {page_url: img_url}


async def capture_and_update_screenshot(page_urls: Set[str]) -> Dict[str, str]:
    # Launch headless browser
    browser = await launch(headless=True)
    tasks = [process_page(page_url, browser) for page_url in page_urls]
    results = await asyncio.gather(*tasks)
    await browser.close()

    response = {k: v for d in results for k, v in d.items()}
    return response
