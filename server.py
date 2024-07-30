import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from typing import List
from util import Change
from util import to_dict
from util import LinkedProperty
from util import Page
from util import PageResponse
from util import Property
from util import UpdatePage
from util import update_pages_with_change


load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)
app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PageWithProperty(Page):
    properties: List[Property]


class ChangeWithHasChange(Change):
    hasChanged: bool


class UpdateChange(ChangeWithHasChange):
    changeId: str


@app.get("/")
async def root():
    return {"message": "Hello, Alertful AI!"}


@app.post("/api/addPages/")
async def add_pages(pages_to_add: List[PageWithProperty]):
    pages = [Page(userId=page.userId, pageUrl=page.pageUrl, query=page.query) for page in pages_to_add]

    # page urls are unique per user.
    properties_per_page_url = {page.pageUrl: page.properties for page in pages_to_add}

    page_dicts = [page.dict() for page in pages]

    # Add Pages to DB
    insert_page_response = supabase.table('Page').insert(page_dicts).execute()
    pages = [UpdatePage(**page) for page in insert_page_response.data]
    pages_by_page_id = dict((page.pageId, page) for page in pages)

    pages = [PageResponse(**page) for page in insert_page_response.data]

    # Insert Updates
    changes_to_insert = [ChangeWithHasChange(summary="", pageId=page.pageId, imageUrl="", hasChanged=False) for page in pages]

    changes_response = supabase.table('Change').insert(to_dict(changes_to_insert)).execute()

    # updates Pages with latest Change
    changes = [UpdateChange(**change) for change in changes_response.data]

    update_page_response = update_pages_with_change(pages_by_page_id, changes, supabase)

    # Insert Properties
    properties_to_insert = []
    for page in [PageResponse(**page) for page in update_page_response.data]:
        if len(properties_per_page_url[page.pageUrl]) == 0:
            properties_to_insert.extend(get_default_properties(pages_id=page.pageId))
        else:
            for entry in properties_per_page_url[page.pageUrl]:
                properties_to_insert.append(
                    LinkedProperty(pageId=page.pageId,
                                   property=entry.property,
                                   type=entry.type,
                                   description=entry.description))
    properties_response = supabase.table('Property').insert(to_dict(properties_to_insert)).execute()

    if properties_response.data:
        return {'message': 'success'}


@app.delete("/api/removePage/{page_id}")
async def remove_page(page_id):
    data, count = supabase.table('Page').delete().eq('pageId', page_id).execute()
    if data:
        return {"data": data, "count": count}


@app.put("/api/updatePage/")
async def update_page(page: UpdatePage):
    data, count = supabase.table('Page').update(page.dict()).eq('pageId', page.pageId).execute()
    if data:
        return {"data": data, "count": count}


@app.get("/api/getAllPages")
async def get_all_pages():
    results = supabase.table('Page').select("*").execute()
    return results


@app.get("/api/getPage/{page_id}")
async def get_page(page_id: str):
    results = supabase.table('Page').select('*').eq('pageId', page_id).execute()
    return results


@app.get("/api/getAllChanges/{page_id}")
async def get_all_changes(page_id: str):
    results = supabase.table('Change').select('*').eq('pageId', page_id).execute()
    return results


@app.post("/api/addChange/")
async def add_change(change: ChangeWithHasChange):
    data, count = supabase.table('Change').insert(change.dict()).execute()
    if data:
        return {"data": data, "count": count}

    return {'message': 'error!'}


@app.post("/api/addProperty/")
async def add_property(entry: LinkedProperty):
    data, count = supabase.table('Property').insert(entry.dict()).execute()
    if data:
        return {"data": data, "count": count}

    return {'message': 'error!'}


def get_default_properties(pages_id: str) -> List[LinkedProperty]:
    summary_property = LinkedProperty(pageId=pages_id,
                                      property="summary",
                                      type="string",
                                      description="Summary of the changes between snapshots.")

    has_change_property = LinkedProperty(pageId=pages_id,
                                         property="has_change",
                                         type="boolean",
                                         description="Snapshots are noticeably different.")

    return [summary_property, has_change_property]
