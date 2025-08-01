from struct_strm.structs.rubric_structs import (
    simulate_stream_rubric_outline_struct,
    simulate_stream_rubric_outline_openai,
    simulate_stream_rubric_final_struct,
    DefaultCriteria,
    DefaultCategory,
    DefaultOutlineRubric,
    DefaultCell,
    DefaultRubric,
)
from struct_strm import tree_sitter_parse
import pytest


@pytest.mark.asyncio
async def test_parse_rubric_json():

    stream = simulate_stream_rubric_outline_struct()
    all_items = []
    async for instance in tree_sitter_parse(DefaultOutlineRubric, stream):
        all_items.append(instance)
    final_item = DefaultOutlineRubric(
        criteria=[
            DefaultCriteria(criteria_value="Write a formal cover letter"),
            DefaultCriteria(criteria_value="Create professional navigation"),
            DefaultCriteria(criteria_value="Identify the logistics and factors"),
        ],
        category=[
            DefaultCategory(category_value="Draft"),
            DefaultCategory(category_value="Developing"),
            DefaultCategory(category_value="Functional"),
        ],
    )

    assert all_items[-1] == final_item


@pytest.mark.asyncio
async def test_parse_rubric_final_json():

    stream = simulate_stream_rubric_final_struct()
    all_items = []
    async for instance in tree_sitter_parse(DefaultRubric, stream):
        all_items.append(instance)
    final_item = DefaultRubric(
        cells=[
            DefaultCell(
                criteria="Write a formal cover letter",
                category="Draft",
                content="Not enough content is present to assess the skill and/or the letter is too far from technical writing and professional standards to recognize.",
            ),
            DefaultCell(
                criteria="Write a formal cover letter",
                category="Functional",
                content="Completed the cover letter by following the expectations of a formal cover letter and addressed it to a relevant stakeholder appropriate to the topic. The letter summarizes the report with the justification of the purpose, key outcomes, and value to stakeholders.",
            ),
            DefaultCell(
                criteria="Create professional navigation",
                category="Functional",
                content="",
            ),
            DefaultCell(
                criteria="Create professional navigation",
                category="Draft",
                content="",
            ),
        ]
    )

    assert all_items[-1] == final_item


@pytest.mark.asyncio
async def test_openai_parse_table_json():

    stream = simulate_stream_rubric_outline_openai()
    all_items = []
    async for instance in tree_sitter_parse(DefaultOutlineRubric, stream):
        all_items.append(instance)

    final_item = DefaultOutlineRubric(
        criteria=[
            DefaultCriteria(criteria_value="Write a formal cover letter"),
            DefaultCriteria(criteria_value="Create professional navigation"),
        ],
        category=[
            DefaultCategory(category_value="Functional"),
            DefaultCategory(category_value="Draft"),
        ],
    )

    assert all_items[-1] == final_item
