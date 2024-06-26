import os
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from supabase import create_client, Client
from typing import List

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)
app = FastAPI()


class Page(BaseModel):
    userId: int
    pageUrl: str
    query: str


class UpdatePage(Page):
    pageId: str


class Change(BaseModel):
    summary: str
    pageId: str
    imageUrl: str


class UpdateChange(Change):
    changeId: str


class PageResponse(BaseModel):
    userId: int
    pageUrl: str
    query: str
    created_at: str
    pageId: str
    updated_at: str


@app.get("/")
async def root():
    return {"message": "Hello, Alertful AI!"}


@app.post("/api/addPages/")
async def add_pages(pages: List[Page]):
    page_dicts = [page.dict() for page in pages]

    # Add Pages to DB
    response = supabase.table('Page').insert(page_dicts).execute()
    data = response.data
    pages = [UpdatePage(**page) for page in data]
    pages_by_page_id = dict((page.pageId, page) for page in pages)

    if data:
        pages = [PageResponse(**page) for page in data]

        changes_to_insert = [{"summary": "", "pageId": page.pageId, "imageUrl": ""} for page in pages]

        changes_response = supabase.table('Change').insert(changes_to_insert).execute()

        # updates Pages with latest Change
        changes = [UpdateChange(**change) for change in changes_response.data]
        pages_to_update = [{"userId": pages_by_page_id[change.pageId].userId,
                            "pageUrl": pages_by_page_id[change.pageId].pageUrl,
                            "query": pages_by_page_id[change.pageId].query,
                            "pageId": change.pageId,
                            "latestChange": change.changeId}
                           for change in changes]

        update_response = supabase.table('Page').upsert(pages_to_update).execute()

        if update_response.data:
            return {'message': 'success'}

    return {'message': 'error!'}


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
