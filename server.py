from typing import List

from dotenv import load_dotenv

import os
from supabase import create_client, Client
from fastapi import FastAPI
from pydantic import BaseModel

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

    if data:
        pages = [PageResponse(**page) for page in data]

        # TODO fetch imageUrls

        change_dicts = [{"summary": "", "pageId": page.pageId, "imageUrl": ""} for page in pages]

        response = supabase.table('Change').insert(change_dicts).execute()

        if response.data:
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
