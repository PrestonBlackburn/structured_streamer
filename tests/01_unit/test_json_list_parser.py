import pytest
from struct_strm import parse_list_json
from struct_strm.structs.list_structs import (
    simulate_stream_list_struct,
    simulate_stream_openai,
)


@pytest.mark.asyncio
async def test_parse_list_json():

    stream = simulate_stream_list_struct()

    all_items = []
    async for items in parse_list_json(stream):
        print(items)
        all_items.append(items)

    expected_items = [
        ["apple"],
        ["apple orange"],
        ["apple orange straw"],
        ["apple orange strawberry"],
        ["apple orange strawberry", "banana"],
        ["apple orange strawberry", "banana kiwi"],
        ["apple orange strawberry", "banana kiwi grape"],
        ["apple orange strawberry", "banana kiwi grape", "mango"],
        ["apple orange strawberry", "banana kiwi grape", "mango pineapple"],
    ]
    last_items = ["apple orange strawberry", "banana kiwi grape", "mango pineapple"]
    print(all_items)
    print(expected_items)
    assert all_items == expected_items
    assert all_items[-1] == last_items


@pytest.mark.asyncio
async def test_openai_parse_list_json():

    stream = simulate_stream_openai()

    all_items = []
    async for items in parse_list_json(stream):
        print(items)
        all_items.append(items)

    last_items = [
        "Hugging Face Transformers: A popular open-source library that provides a wide range etc....",
        "Llama.cpp: A C++ implementation for running LLaMA and other large language etc....",
    ]

    assert all_items[-1] == last_items
