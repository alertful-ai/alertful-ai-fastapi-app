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


class UpdatePage(Page):
    pageId: str


class PageWithChange(UpdatePage):
    latestChange: str


class PageResponse(Page):
    created_at: str
    pageId: str
    updated_at: str


class Summary(BaseModel):
    has_change: bool
    summary: str


def update_pages_with_change(page_by_page_id, changes, supabase):
    pages_to_update = [PageWithChange(userId=page_by_page_id[change.pageId].userId,
                                      pageUrl=page_by_page_id[change.pageId].pageUrl,
                                      query=page_by_page_id[change.pageId].query,
                                      pageId=change.pageId,
                                      latestChange=change.changeId)
                       for change in changes]

    return supabase.table('Page').upsert(to_dict(pages_to_update)).execute()


def to_dict(obj_list) -> List[dict]:
    # Use a list comprehension to apply .dict() to each object in the list
    return [obj.dict() for obj in obj_list]
