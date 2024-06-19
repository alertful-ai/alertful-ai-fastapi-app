import os
from dotenv import load_dotenv
from supabase import create_client, Client
from pydantic import BaseModel

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


class Page(BaseModel):
    page_url: str
    page_query: str
    page_id: str


# load all pages
pageResponse = supabase.table('Page').select("pageId", "pageUrl", "query").execute()
pages = [Page(**page) for page in pageResponse.data]

# TODO: generate image_url from page_url
image_url = ""
# generate update for each page
# TODO: fetch summary from chatGPT from page_query
summary = ""

# create Changes
change_dicts = [{"summary": summary, "pageId": page.page_id, "imageUrl": image_url} for page in pages]
response = supabase.table('Change').insert(change_dicts).execute()
