import pytest
from struct_strm.structs.form_structs import (
    simulate_stream_form_struct,
    simulate_stream_form_openai,
    DefaultFormStruct,
    DefaultFormItem,
    DataclassDefaultFormItem,
    DataclassDefaultFormStruct,
)
from struct_strm.partial_parser import tree_sitter_parse
from struct_strm.compat import to_json


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
async def test_parse_form_json_dataclass():
    stream = simulate_stream_form_struct(struct_type="dataclass")
    all_items = []
    async for instance in tree_sitter_parse(DataclassDefaultFormStruct, stream):
        all_items.append(instance)
    final_item = DataclassDefaultFormStruct(
        form_fields=[
            DataclassDefaultFormItem(
                field_name="fruits", field_placeholder="apple orange strawberry"
            ),
            DataclassDefaultFormItem(
                field_name="appliance", field_placeholder="blender mixer toaster"
            ),
            DataclassDefaultFormItem(
                field_name="dishes", field_placeholder="plate bowl"
            ),
        ]
    )
    final_item = to_json(final_item)
    generated_item = to_json(all_items[-1])
    assert generated_item == final_item


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
