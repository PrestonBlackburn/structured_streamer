import pytest
from struct_strm import parse_table_json_ts
from struct_strm.structs.table_structs import (
    simulate_stream_table_struct,
    simulate_stream_table_openai,
    ExampleRow,
)


@pytest.mark.asyncio
async def test_parse_table_json():

    stream = simulate_stream_table_struct()

    all_items = []
    async for items in parse_table_json_ts(stream, ExampleRow):
        print(items)
        all_items.append(items)

    # expected_items = [
    # ]
    last_items = {
        0: {"title": "Akira", "genre": "action, cyberpunk, horror", "rating": "5"},
        1: {
            "title": "2001: A Space Odyssey",
            "genre": "Sci-fi, Suspense",
            "rating": "5",
        },
        2: {"title": "Gattaca", "genre": "Sci-fi, Thriller", "rating": "4"},
    }
    print(all_items)
    # print(expected_items)
    # assert all_items == expected_items
    assert all_items[-1] == last_items


@pytest.mark.asyncio
async def test_openai_parse_table_json():

    stream = simulate_stream_table_openai()

    all_items = []
    async for items in parse_table_json_ts(stream, ExampleRow):
        print(items)
        all_items.append(items)

    last_items = {
        0: {"title": "Akira", "genre": "action, cyberpunk, horror.", "rating": "5"},
        1: {
            "title": "2001: A Space Odyssey",
            "genre": "Sci-fi, Suspense.",
            "rating": "5",
        },
    }
    assert all_items[-1] == last_items
