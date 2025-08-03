from pydantic import BaseModel
from enum import Enum
from typing import AsyncGenerator
import asyncio

# this will need to be dynamic -
# so based on the headers we get back we can construct a class dynamically
# This is actually a 2 parter, since we need to do one generation after another - will need another approach


class DefaultCriteria(BaseModel):
    # "Y"
    criteria_value: str = ""


class DefaultCategory(BaseModel):
    # "X"
    category_value: str = ""


class DefaultOutlineRubric(BaseModel):
    category: list[DefaultCategory] = []
    criteria: list[DefaultCriteria] = []



def create_rubric_enums(
    generated_outline: DefaultOutlineRubric,
) -> type:
    # these would be provided for openai input to restrict outputs to previous categories
    # need to implement more cleaning for these later
    criteria_enum_cls = Enum(
        "ReturnedCriteria",
        {
            (item.criteria.replace(" ", "_"), item.criteria)
            for item in generated_outline.criteria
        },
        type=str,
    )

    category_enum_cls = Enum(
        "ReturnedCategory",
        {
            (item.category.replace(" ", "_"), item.category)
            for item in generated_outline.category
        },
        type=str,
    )

    class ScopedRubricCell(BaseModel):
        criteria: criteria_enum_cls
        category: category_enum_cls
        content: str

    class ScopedDefaultRubric(BaseModel):
        cells: list[ScopedRubricCell] = []

    return ScopedDefaultRubric


# we don't need to restrict the response since it is alredy being restricted upstream
class DefaultCell(BaseModel):
    # criteria and category must be enums
    category: str = ""
    criteria: str = ""
    content: str = ""


class DefaultRubric(BaseModel):
    cells: list[DefaultCell] = []


async def simulate_stream_rubric_outline_struct(
    interval_sec: float = 0.0,
) -> AsyncGenerator[str, None]:
    # Simulate a stream from a structured generator like OpenAI
    rubric_struct = DefaultOutlineRubric(
        criteria=[
            DefaultCriteria(criteria_value="Write &a &formal &cover &letter"),
            DefaultCriteria(criteria_value="Create &professional &navigation"),
            DefaultCriteria(criteria_value="Identify &the &logistics &and &factors"),
        ],
        category=[
            DefaultCategory(category_value="Draft"),
            DefaultCategory(category_value="Developing"),
            DefaultCategory(category_value="Functional"),
        ],
    )
    json_response = rubric_struct.model_dump_json()
    # we want to split on "{", ":", "," and " "
    json_response = (
        json_response.replace("{", "&{&")
        .replace(":", "&:&")
        .replace(",", "&,&")
        .replace("}", "&}&")
    )
    stream_response = json_response.split("&")
    for item in stream_response:
        item = item.replace("&", "")
        await asyncio.sleep(interval_sec)
        yield item


async def simulate_stream_rubric_final_struct(
    interval_sec: float = 0.0,
) -> AsyncGenerator[str, None]:
    # bootstrap enums

    rubric_final_struct = DefaultRubric(
        cells=[
            DefaultCell(
                criteria="Write &a &formal &cover &letter",
                category="Draft",
                content="Not enough content is present to assess the skill and/or the letter is too far from technical writing and professional standards to recognize.",
            ),
            DefaultCell(
                criteria="Create &professional &navigation",
                category="Draft",
                content="Navigation sucked",
            ),
            DefaultCell(
                criteria="Identify &the &logistics &and &factors",
                category="Draft",
                content="Minimal logistics and factors are identified, or the information is not relevant to the topic.",
            ),
            DefaultCell(
                criteria="Write &a &formal &cover &letter",
                category="Developing",
                content="room for improvement",
            ),
            DefaultCell(
                criteria="Create &professional &navigation",
                category="Developing",
                content="Navigation was ok",
            ),
            DefaultCell(
                criteria="Identify &the &logistics &and &factors",
                category="Developing",
                content="OK logistics and factors are identified",
            ),
            DefaultCell(
                criteria="Write &a &formal &cover &letter",
                category="Functional",
                content="Completed the cover letter by following the expectations of a formal cover letter and addressed it to a relevant stakeholder appropriate to the topic. The letter summarizes the report with the justification of the purpose, key outcomes, and value to stakeholders.",
            ),
            DefaultCell(
                criteria="Create &professional &navigation",
                category="Functional",
                content="Did great with the navigation",
            ),
            DefaultCell(
                criteria="Identify &the &logistics &and &factors",
                category="Functional",
                content="Much wow",
            ),
        ]
    )
    json_response = rubric_final_struct.model_dump_json()
    json_response = (
        json_response.replace("{", "&{&")
        .replace(":", "&:&")
        .replace(",", "&,&")
        .replace("}", "&}&")
    )
    stream_response = json_response.split("&")
    for item in stream_response:
        item = item.replace("&", "")
        await asyncio.sleep(interval_sec)
        yield item


async def simulate_stream_rubric_outline_openai(
    interval_sec: float = 0.0,
) -> AsyncGenerator[str, None]:
    response_tokens = [
        " ",
        '{"',
        "criteria",
        '":[',
        '{"',
        "criteria_value",
        '":"',
        "Write",
        " a",
        " formal",
        " cover" " letter",
        '"',
        '},{"',
        "criteria_value",
        '":"',
        "Create",
        " professional",
        " navigation",
        '"',
        "}",
        ']"',
        "category",
        '":[',
        '{"',
        "category_value",
        '":"',
        "Functional",
        '"',
        '},{"',
        "category_value",
        '":"',
        "Draft",
        '"',
        "}",
        "]}",
    ]

    for item in response_tokens:
        await asyncio.sleep(interval_sec)
        yield item
