from typing import List

from pydantic import BaseModel


class Property(BaseModel):
    property: str
    type: str
    description: str


class LinkedProperty(Property):
    pageId: str


class Page(BaseModel):
    userId: str
    pageUrl: str
    query: str


class PageResponse(Page):
    created_at: str
    pageId: str
    updated_at: str


class Summary(BaseModel):
    has_change: bool
    summary: str


def to_dict(obj_list) -> List[dict]:
    # Use a list comprehension to apply .dict() to each object in the list
    return [obj.dict() for obj in obj_list]
