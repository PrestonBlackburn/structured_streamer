import asyncio
from typing import AsyncGenerator
from pydantic import BaseModel
from dataclasses import dataclass, field
from struct_strm.compat import to_json


class DefaultSwitchState(BaseModel):
    # Use strings for parser compatibility ("on"/"off")
    state: str = "off"
    label: str = "Enable switch"


@dataclass
class DataclassDefaultSwitchState:
    state: str = "off"
    label: str = "Enable switch"


async def simulate_stream_switch_state(
    interval_sec: float = 0.0, struct_type: str = "pydantic"
) -> AsyncGenerator[str, None]:

    if struct_type == "pydantic":
        model = DefaultSwitchState(state="off", label="Enable switch")
    elif struct_type == "dataclass":
        model = DataclassDefaultSwitchState(state="off", label="Enable switch")
    else:
        raise ValueError(f"Invalid struct type: {struct_type}")

    json_response = to_json(model)
    # Split by common JSON delimiters
    json_response = (
        json_response.replace("{", "&{&")
        .replace(":", "&:&")
        .replace(",", "&,&")
        .replace("}", "&}&")
    )
    stream_response = json_response.split("&")
    for item in stream_response:
        item = item.replace("&", "")
        await asyncio.sleep(interval_sec)
        yield item


async def simulate_stream_switch_openai(
    interval_sec: float = 0.0,
) -> AsyncGenerator[str, None]:

    response_tokens = [
        " ",
        '{"',
        "state",
        '":"',
        "off",
        '"',
        ", ",
        '"',
        "label",
        '":"',
        "Enable",
        " switch",
        '"',
        "}",
    ]

    for item in response_tokens:
        await asyncio.sleep(interval_sec)
        yield item


