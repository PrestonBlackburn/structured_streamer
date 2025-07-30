import pytest
from struct_strm.partial_parser import tree_sitter_parse, query_tree_l1, query_tree_l2
from dataclasses import dataclass, field
from struct_strm.structs.list_structs import (
    simulate_stream_list_struct,
    simulate_stream_openai,
    DefaultListItem,
    DefaultListStruct,
)
from struct_strm.structs.form_structs import (
    simulate_stream_form_struct,
    DefaultFormItem,
    DefaultFormStruct,
)

from struct_strm.structs.table_structs import (
    simulate_stream_table_struct,
    ExampleRow,
    ExampleTableStruct,
)


@pytest.mark.asyncio
async def test_parse_list_json_pydantic():

    stream = simulate_stream_list_struct()

    all_items = []
    async for instance in tree_sitter_parse(DefaultListStruct, stream):
        all_items.append(instance)

    final_item = DefaultListStruct(
        items=[
            DefaultListItem(item="apple orange strawberry"),
            DefaultListItem(item="banana kiwi grape"),
            DefaultListItem(item="mango pineapple"),
        ]
    )

    assert all_items[-1] == final_item


@pytest.mark.asyncio
async def test_parse_list_json_pydantic():

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


@pytest.mark.asyncio
async def test_parse_form_json_pydantic():
    stream = simulate_stream_form_struct()
    all_items = []
    async for instance in tree_sitter_parse(DefaultFormStruct, stream):
        all_items.append(instance)
    final_item = DefaultFormStruct(
        form_fields=[
            DefaultFormItem(
                field_name="fruits", field_placeholder="apple orange strawberry"
            ),
            DefaultFormItem(
                field_name="appliance", field_placeholder="blender mixer toaster"
            ),
            DefaultFormItem(field_name="dishes", field_placeholder="plate bowl"),
        ]
    )
    assert all_items[-1] == final_item


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
async def test_parse_list_json_dataclass():
    @dataclass
    class ListItem:
        item: str = ""

    @dataclass
    class ListStruct:
        items: list[ListItem] = field(default_factory=lambda: [])

    stream = simulate_stream_list_struct()
    all_items = []
    async for instance in tree_sitter_parse(ListStruct, stream):
        all_items.append(instance)

    # need to return + populate nested classes for dataclasses still
    final_item = ListStruct(
        items=[
            {"item": "apple orange strawberry"},
            {"item": "banana kiwi grape"},
            {"item": "mango pineapple"},
        ]
    )
    assert all_items[-1] == final_item
