import asyncio
import pytest

from struct_strm.structs.dropdown_structs import (
    DefaultDropdown,
    simulate_stream_dropdown,
    simulate_stream_dropdown_openai,
)
from struct_strm.partial_parser import tree_sitter_parse


@pytest.mark.asyncio
async def test_dropdown_parsing_pydantic_simulator():
    stream = simulate_stream_dropdown(interval_sec=0.0, struct_type="pydantic")
    parsed_values = []
    async for dd in tree_sitter_parse(DefaultDropdown, stream):
        parsed_values.append(
            (
                dd.dropdown_label,
                dd.selected,
                [(o.value, o.label) for o in dd.options],
            )
        )

    assert parsed_values, "No values parsed from dropdown stream"
    final_label, final_selected, final_options = parsed_values[-1]
    assert final_label == "Select an option"
    assert final_selected == "opt_b"
    assert ("opt_a", "Option A") in final_options
    assert ("opt_b", "Option B") in final_options


@pytest.mark.asyncio
async def test_dropdown_parsing_openai_like_tokens():
    stream = simulate_stream_dropdown_openai(interval_sec=0.0)
    parsed_values = []
    async for dd in tree_sitter_parse(DefaultDropdown, stream):
        parsed_values.append(
            (
                dd.dropdown_label,
                dd.selected,
                [(o.value, o.label) for o in dd.options],
            )
        )

    assert parsed_values, "No values parsed from OpenAI-like dropdown stream"
    final_label, final_selected, final_options = parsed_values[-1]
    assert final_label == "Select an option"
    assert final_selected == "opt_b"
    assert ("opt_a", "Option A") in final_options
    assert ("opt_b", "Option B") in final_options


