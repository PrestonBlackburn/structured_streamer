import pytest
from struct_strm.structs.form_structs import (
    simulate_stream_form_struct,
    simulate_stream_form_openai,
    DefaultFormStruct,
    DefaultFormItem,
)
from struct_strm.partial_parser import tree_sitter_parse


@pytest.mark.asyncio
async def test_parse_form_json():
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
async def test_openai_parse_form_json():

    stream = simulate_stream_form_openai()

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
        ]
    )

    assert all_items[-1] == final_item
