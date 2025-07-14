from pydantic import BaseModel
from typing import List

# this will need to be dynamic -
# so based on the headers we get back we can construct a class dynamically
# This is actually a 2 parter, since we need to do one generation after another - will need another approach


class DefaultCriteria(BaseModel):
    # "Y"
    criteria: str


class DefaultCategory(BaseModel):
    # "X"
    category: str


class DefaultOutlineRubric:
    criteria: DefaultCriteria
    category: DefaultCategory


class DefaultCell(BaseModel):
    criteria: DefaultCriteria
    category: DefaultCategory
    content: str


class DefaultRubric:
    cells: List[DefaultCell]


# ex: table={"header": [{"header": "column_a"}, {"header": "column_b"}], "rows": [{"row": "apple orange"}, {"row": "banana kiwi grape"}, {"row": "mango pineapple"}]
