import pytest
from struct_strm.structs.list_structs import (
    simulate_stream_list_struct,
    simulate_stream_openai,
    DefaultListStruct,
    DefaultListItem,
)
from struct_strm.partial_parser import tree_sitter_parse

@pytest.mark.asyncio
async def test_parse_list_json():

    stream = simulate_stream_list_struct()

    all_items = []
    async for instance in tree_sitter_parse(DefaultListStruct, stream):
        all_items.append(instance)

    some_expected_items = [
        DefaultListStruct(
            items=[
                DefaultListItem(item="apple "),
            ]
        ),
        DefaultListStruct(
            items=[
                DefaultListItem(item="apple orange strawberry"),
            ]
        ),
        DefaultListStruct(
            items=[
                DefaultListItem(item="apple orange strawberry"),
                DefaultListItem(item="banana "),
            ]
        ),
        DefaultListStruct(
            items=[
                DefaultListItem(item="apple orange strawberry"),
                DefaultListItem(item="banana kiwi grape"),
            ]
        ),
        DefaultListStruct(
            items=[
                DefaultListItem(item="apple orange strawberry"),
                DefaultListItem(item="banana kiwi grape"),
                DefaultListItem(item="mango pineapple"),
            ]
        ),
    ]

    some_unexpected_items = [
        DefaultListStruct(
            items=[
                DefaultListItem(item="banana kiwi grape"),
                DefaultListItem(item="mango pineapple"),
            ]
        ),
        DefaultListStruct(
            items=[
                DefaultListItem(item="strawberry"),
            ]
        ),
        DefaultListStruct(
            items=[
                DefaultListItem(item="mango pineapple"),
            ]
        ),

    ]

    for item in some_expected_items:
    
        assert str(item) in [str(cls) for cls in all_items]

    for item in some_unexpected_items:
        assert str(item) not in [str(cls) for cls in all_items]




@pytest.mark.asyncio
async def test_openai_parse_list_json():

    stream = simulate_stream_openai()

    all_items = []
    async for instance in tree_sitter_parse(DefaultListStruct, stream):
        all_items.append(instance)

    final_item = DefaultListStruct(
        items=[
            DefaultListItem(
                item="Hugging Face Transformers: A popular open-source library that provides a wide range etc...."
            ),
            DefaultListItem(
                item="Llama.cpp: A C++ implementation for running LLaMA and other large language etc...."
            ),
        ]
    )

    assert all_items[-1] == final_item