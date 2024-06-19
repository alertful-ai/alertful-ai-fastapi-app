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

# load all pages

# generate update for each page
