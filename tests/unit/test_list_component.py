
import pytest
from struct_strm.ui_components import ListComponent
from struct_strm.default_structs import simulate_stream_list_struct

@pytest.mark.asyncio
async def test_list_component_partial_render():
    component = ListComponent()
    stream = simulate_stream_list_struct()
    async for _ in component.render(response_stream=stream):
        pass

    expected_items = ["apple orange", "banana kiwi grape", "mango pineapple"]
    assert component.items == expected_items
