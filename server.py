import os
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from supabase import create_client, Client
from typing import List
from fastapi.middleware.cors import CORSMiddleware

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


class Property(BaseModel):
    property: str
    type: str
    description: str


class Page(BaseModel):
    userId: str
    pageUrl: str
    query: str


class AddPage(Page):
    properties: List[Property]


class UpdatePage(Page):
    pageId: str


class Change(BaseModel):
    summary: str
    pageId: str
    imageUrl: str
    hasChanged: bool


class UpdateChange(Change):
    changeId: str


class PageResponse(BaseModel):
    userId: str
    pageUrl: str
    query: str
    created_at: str
    pageId: str
    updated_at: str


@app.get("/")
async def root():
    return {"message": "Hello, Alertful AI!"}


@app.post("/api/addPages/")
async def add_pages(pages_to_add: List[AddPage]):
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
    changes_to_insert = [{"summary": "",
                          "pageId": page.pageId,
                          "imageUrl": "",
                          "hasChanged": False}
                         for page in pages]

    changes_response = supabase.table('Change').insert(changes_to_insert).execute()

    # updates Pages with latest Change
    changes = [UpdateChange(**change) for change in changes_response.data]
    pages_to_update = [{"userId": pages_by_page_id[change.pageId].userId,
                        "pageUrl": pages_by_page_id[change.pageId].pageUrl,
                        "query": pages_by_page_id[change.pageId].query,
                        "pageId": change.pageId,
                        "latestChange": change.changeId}
                       for change in changes]

    update_page_response = supabase.table('Page').upsert(pages_to_update).execute()

    # Insert Properties
    properties_to_insert = []
    for page in [PageResponse(**page) for page in update_page_response.data]:
        for entry in properties_per_page_url[page.pageUrl]:
            properties_to_insert.append({"pageId": page.pageId,
                                         "property": entry.property,
                                         "type": entry.type,
                                         "description": entry.description})
    properties_response = supabase.table('Property').insert(properties_to_insert).execute()

    if properties_response.data:
        return {'message': 'success'}


@app.delete("/api/removePage/{page_id}")
async def remove_page(page_id):
    print("PAGE ID", page_id)
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
async def add_change(change: Change):
    data, count = supabase.table('Change').insert(change.dict()).execute()
    if data:
        return {"data": data, "count": count}

    return {'message': 'error!'}
