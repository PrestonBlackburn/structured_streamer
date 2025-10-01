import pytest
from struct_strm.structs.table_structs import (
    simulate_stream_table_struct,
    simulate_stream_table_openai,
    ExampleRow,
    ExampleTableStruct,
    DataclassExampleRow,
    DataclassExampleTableStruct,
)
from struct_strm.partial_parser import tree_sitter_parse
from struct_strm.compat import to_json


@pytest.mark.asyncio
async def test_parse_table_json_pydantic():

    stream = simulate_stream_table_struct()
    all_items = []
    async for instance in tree_sitter_parse(ExampleTableStruct, stream):
        all_items.append(instance)
    final_item = ExampleTableStruct(
        table=[
            ExampleRow(title="Akira", genre="action, cyberpunk, horror", rating="5"),
            ExampleRow(
                title="2001: A Space Odyssey", genre="Sci-fi, Suspense", rating="5"
            ),
            ExampleRow(title="Gattaca", genre="Sci-fi, Thriller", rating="4"),
        ]
    )
    assert all_items[-1] == final_item


@pytest.mark.asyncio
async def test_parse_table_json_dataclass():
    stream = simulate_stream_table_struct(struct_type="dataclass")
    all_items = []
    async for instance in tree_sitter_parse(DataclassExampleTableStruct, stream):
        all_items.append(instance)
    final_item = DataclassExampleTableStruct(
        table=[
            DataclassExampleRow(
                title="Akira", genre="action, cyberpunk, horror", rating="5"
            ),
            DataclassExampleRow(
                title="2001: A Space Odyssey", genre="Sci-fi, Suspense", rating="5"
            ),
            DataclassExampleRow(title="Gattaca", genre="Sci-fi, Thriller", rating="4"),
        ]
    )
    final_item = to_json(final_item)
    generated_item = to_json(all_items[-1])
    assert generated_item == final_item


@pytest.mark.asyncio
async def test_openai_parse_table_json():

    stream = simulate_stream_table_openai()
    all_items = []
    async for instance in tree_sitter_parse(ExampleTableStruct, stream):
        all_items.append(instance)
    final_item = ExampleTableStruct(
        table=[
            ExampleRow(title="Akira", genre="action, cyberpunk, horror.", rating="5"),
            ExampleRow(
                title="2001: A Space Odyssey", genre="Sci-fi, Suspense.", rating="5"
            ),
        ]
    )
    assert all_items[-1] == final_item
