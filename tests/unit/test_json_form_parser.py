import pytest
from struct_strm import parse_form_json_fsm
from struct_strm.structs.form_structs import (
    simulate_stream_form_struct,
    simulate_stream_form_openai
)
@pytest.mark.asyncio
async def test_parse_form_json():

    stream = simulate_stream_form_struct()

    all_items = []
    async for items in parse_form_json_fsm(stream):
        print(items)
        all_items.append(items)

    # expected_items = [
    # ]
    last_items = {0: {'field_name': 'fruits', 'field_placeholder': 'apple orange strawberry'}, 1: {'field_name': 'appliance', 'field_placeholder': 'blender mixer toaster'}, 2: {'field_name': 'dishes', 'field_placeholder': 'plate bowl'}}
    print(all_items)
    # print(expected_items)
    # assert all_items == expected_items
    assert all_items[-1] == last_items

@pytest.mark.asyncio
async def test_openai_parse_form_json():

    stream = simulate_stream_form_openai()
    
    all_items = []
    async for items in parse_form_json_fsm(stream):
        print(items)
        all_items.append(items)

    last_items = {0: {'field_name': ':fruits', 'field_placeholder': 'apple orange strawberry.'}, 1: {'field_name': 'appliance', 'field_placeholder': 'blender mixer toaster.'}}
    assert all_items[-1] == last_items