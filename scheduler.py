import asyncio
import os
from collections import defaultdict
from dotenv import load_dotenv
from query import query_chat_gpt
from screenshot import capture_and_update_screenshot
from supabase import create_client, Client
from typing import List, Dict
from util import Change
from util import Summary
from util import LinkedProperty
from util import PageWithChange
from util import update_pages_with_change

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


class ChangeWithId(Change):
    changeId: str


def get_properties_by_page_id() -> Dict[str, List[LinkedProperty]]:
    properties_response = (supabase.table('Property')
                           .select('pageId', 'property', 'type', 'description')
                           .execute())
    properties = [LinkedProperty(**entry) for entry in properties_response.data]
    grouped_properties = defaultdict(list)
    for prop in properties:
        grouped_properties[prop.pageId].append(prop)
    return dict(grouped_properties)


# load all pages
page_response = supabase.table('Page').select('*').execute()
pages = [PageWithChange(**page) for page in page_response.data]
page_by_page_id = dict((page.pageId, page) for page in pages)

page_urls = set([page.pageUrl for page in pages])
page_to_image_urls = asyncio.run(capture_and_update_screenshot(page_urls))

# pages with previous snapshot
latestChangeIds = [page.latestChange for page in pages]
latest_changes_response = (supabase.table('Change').select("*")
                           .in_('changeId', latestChangeIds).execute())
latest_changes = [ChangeWithId(**change) for change in latest_changes_response.data]
previous_page_snapshot = {change.pageId: change.imageUrl for change in latest_changes}
pages_to_summarize = [page_by_page_id[change.pageId] for change in latest_changes
                      if change.imageUrl != "" and change.summary != ""]

properties_by_page_id = get_properties_by_page_id()

# generate update for each page
summary_by_page_id = {}
for page in pages_to_summarize:
    previous_snapshot = previous_page_snapshot[page.pageId]
    current_snapshot = page_to_image_urls[page.pageUrl]
    query = page.query
    summary = query_chat_gpt(previous_snapshot, current_snapshot, query, properties_by_page_id[page.pageId])
    summary_by_page_id[page.pageId] = summary

# create Changes
default_summary = Summary(has_change=False, summary="Initial Snapshot")
changes_to_insert = [{"summary": summary_by_page_id.get(page.pageId, default_summary).summary,
                      "pageId": page.pageId,
                      "imageUrl": page_to_image_urls[page.pageUrl],
                      "hasChanged": summary_by_page_id.get(page.pageId, default_summary).has_change}
                     for page in pages]
changes_response = supabase.table('Change').insert(changes_to_insert).execute()

# updates Pages with latest Change
changes = [ChangeWithId(**change) for change in changes_response.data]
update_pages_with_change(page_by_page_id, changes, supabase)
