import os
from dotenv import load_dotenv
from supabase import create_client, Client
from pydantic import BaseModel

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


class Page(BaseModel):
    pageUrl: str
    query: str
    pageId: str


# load all pages
page_response = supabase.table('Page').select("pageId", "pageUrl", "query").execute()
pages = [Page(**page) for page in page_response.data]

# TODO: generate image_url from page_url
image_url = ""
# generate update for each page
# TODO: fetch summary from chatGPT from page_query
summary = ""

# create Changes
changes_to_insert = [{"summary": summary, "pageId": page.pageId, "imageUrl": image_url} for page in pages]
response = supabase.table('Change').insert(changes_to_insert).execute()
