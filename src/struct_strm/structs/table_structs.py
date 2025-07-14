import asyncio
import time
from typing import List, AsyncGenerator
from pydantic import BaseModel


def get_struct_keys(struct: BaseModel) -> List[str]:
    return list(struct.model_fields.keys())


class DefaultRow(BaseModel):
    row: str


class DefaultHeaders(BaseModel):
    header: str


class DefaultTableStruct(BaseModel):
    # mostly just for testing
    header: List[DefaultHeaders]
    items: List[DefaultRow]
    # ex: table={"header": [{"header": "column_a"}, {"header": "column_b"}], "rows": [{"row": "apple orange"}, {"row": "banana kiwi grape"}, {"row": "mango pineapple"}]
