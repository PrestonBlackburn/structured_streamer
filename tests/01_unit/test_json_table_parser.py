import pytest
from struct_strm.structs.table_structs import (
    simulate_stream_table_struct,
    simulate_stream_table_openai,
    ExampleRow,
    ExampleTableStruct,
)
from struct_strm.partial_parser import tree_sitter_parse


@pytest.mark.asyncio
async def test_parse_table_json():

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
