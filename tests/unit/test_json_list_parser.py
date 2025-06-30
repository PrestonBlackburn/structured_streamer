import pytest
from struct_strm import parse_list_json
from struct_strm.default_structs import simulate_stream_list_struct

@pytest.mark.asyncio
async def test_parse_list_json():

    stream = simulate_stream_list_struct()

    all_items = []
    async for items in parse_list_json(stream):
        print(items)
        all_items.append(items)

    expected_items = [
        ['apple'],
        ['apple orange'],
        ['apple orange', 'banana'],
        ['apple orange', 'banana kiwi'],
        ['apple orange', 'banana kiwi grape'],
        ['apple orange', 'banana kiwi grape', 'mango'],
        ['apple orange', 'banana kiwi grape', 'mango pineapple']
    ]
    last_items = ["apple orange", "banana kiwi grape", "mango pineapple"]
    assert all_items == expected_items
    assert last_items == expected_items[-1]