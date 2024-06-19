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
pageResponse = supabase.table('Page').select("pageId", "pageUrl", "query").execute()
pages = [Page(**page) for page in pageResponse.data]

# generate update for each page
# TODO: fetch summary from chatGPT
summary = ""
# TODO: generate imageUrl
imageUrl = ""

# create Changes
change_dicts = [{"summary": summary, "pageId": page.pageId, "imageUrl": imageUrl} for page in pages]
response = supabase.table('Change').insert(change_dicts).execute()
