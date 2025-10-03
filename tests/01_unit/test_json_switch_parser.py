import asyncio
import pytest

from struct_strm.structs.switch_structs import (
    DefaultSwitchState,
    simulate_stream_switch_state,
    simulate_stream_switch_openai,
)
from struct_strm.partial_parser import tree_sitter_parse


@pytest.mark.asyncio
async def test_switch_l1_parsing_pydantic_simulator():
    stream = simulate_stream_switch_state(interval_sec=0.0, struct_type="pydantic")
    parsed_values = []
    async for state in tree_sitter_parse(DefaultSwitchState, stream):
        parsed_values.append((state.state, state.label))

    # Should converge to final values
    assert parsed_values, "No values parsed from stream"
    final_state, final_label = parsed_values[-1]
    assert final_state == "on"
    assert final_label == "Enable setting"


@pytest.mark.asyncio
async def test_switch_l1_parsing_openai_like_tokens():
    stream = simulate_stream_switch_openai(interval_sec=0.0)
    parsed_values = []
    async for state in tree_sitter_parse(DefaultSwitchState, stream):
        parsed_values.append((state.state, state.label))

    assert parsed_values, "No values parsed from OpenAI-like stream"
    final_state, final_label = parsed_values[-1]
    assert final_state == "on"
    assert final_label == "Enable setting"


