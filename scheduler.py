import asyncio
import os
from dotenv import load_dotenv
from screenshot import capture_and_update_screenshot
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
    userId: int
    latestChange: str


class Change(BaseModel):
    changeId: str
    pageId: str
    summary: str
    imageUrl: str


# load all pages
page_response = supabase.table('Page').select('*').execute()
pages = [Page(**page) for page in page_response.data]
page_by_page_id = dict((page.pageId, page) for page in pages)

page_urls = set([page.pageUrl for page in pages])
page_to_image_urls = asyncio.run(capture_and_update_screenshot(page_urls))

# pages with previous snapshot
latestChangeIds = [page.latestChange for page in pages]
latest_changes_response = (supabase.table('Change').select("*")
                           .in_('changeId', latestChangeIds).execute())
latest_changes = [Change(**change) for change in latest_changes_response.data]
pages_to_summarize = [page_by_page_id[change.pageId] for change in latest_changes
                      if change.imageUrl != "" and change.summary != ""]

# generate update for each page
# TODO: fetch summary from chatGPT from page_query
summary_by_page_id = dict((page.pageId, "summary to fetch from chat GPT") for page in pages_to_summarize)

# create Changes
changes_to_insert = [{"summary": summary_by_page_id.get(page.pageId, "Initial Snapshot"),
                      "pageId": page.pageId,
                      "imageUrl": page_to_image_urls[page.pageUrl]}
                     for page in pages]
changes_response = supabase.table('Change').insert(changes_to_insert).execute()

# updates Pages with latest Change
changes = [Change(**change) for change in changes_response.data]
pages_to_update = [{"userId": page_by_page_id[change.pageId].userId,
                    "pageUrl": page_by_page_id[change.pageId].pageUrl,
                    "query": page_by_page_id[change.pageId].query,
                    "pageId": change.pageId,
                    "latestChange": change.changeId}
                   for change in changes]

update_response = supabase.table('Page').upsert(pages_to_update).execute()
