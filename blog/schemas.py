from ninja import Schema
from typing import Optional
from datetime import datetime


class CategorySchema(Schema):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CategoryCreateSchema(Schema):
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None


class ArticleSchema(Schema):
    id: int
    title: str
    slug: str
    content: str
    author_id: int
    author_username: str
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    published: bool

    class Config:
        from_attributes = True


class ArticleCreateSchema(Schema):
    title: str
    slug: Optional[str] = None
    content: str
    category_id: Optional[int] = None
    published: bool = True


class ArticleUpdateSchema(Schema):
    title: Optional[str] = None
    slug: Optional[str] = None
    content: Optional[str] = None
    category_id: Optional[int] = None
    published: Optional[bool] = None


class CommentSchema(Schema):
    id: int
    article_id: int
    article_title: str
    author_id: int
    author_username: str
    content: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CommentCreateSchema(Schema):
    article_id: int
    content: str


class CommentUpdateSchema(Schema):
    content: str


class UserSchema(Schema):
    id: int
    username: str
    date_joined: datetime

    class Config:
        from_attributes = True


class UserRegisterSchema(Schema):
    username: str
    password: str

