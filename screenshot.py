import uuid
from dotenv import load_dotenv
import os
from pyppeteer import launch
from supabase import create_client, Client
import asyncio
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
async def capture_screenshot(page_url, file_path):
    browser = await launch(headless=True)
    page = await browser.newPage()
    await page.setViewport({'width': 1280, 'height': 800})
    await page.goto(page_url, {'waitUntil': 'networkidle2'})
    await page.screenshot({'path': file_path, 'fullPage': True})
    await browser.close()


async def upload_to_supabase(file_name: str, file_path: str):
    try:
        s3.upload_file(file_path, BUCKET_NAME, file_name, ExtraArgs={'ContentType': 'image/png'})
        file_url = f"{image_url}/{file_name}"
        print(f"File {file_name} uploaded to {BUCKET_NAME}/{file_name}")
        return file_url
    except Exception as e:
        print(f"Error uploading file: {e}")


async def capture_and_update_screenshot(page_url):
    file_name = f'{uuid.uuid4()}.png'
    local_file_path = f'screenshots/{file_name}'

    await capture_screenshot(page_url, local_file_path)
    file_url = await upload_to_supabase(file_name, local_file_path)

    return {'message': 'successful', 'file_url': file_url}
