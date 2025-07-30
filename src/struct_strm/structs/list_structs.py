import asyncio
import time
from typing import List, AsyncGenerator
from pydantic import BaseModel
from dataclasses import dataclass, field


class DefaultListItem(BaseModel):
    item: str = ""


class DefaultListStruct(BaseModel):
    # mostly just for testing
    items: list[DefaultListItem] = []
    # ex: itesms=[{"item": "apple orange"}, {"item2": "banana kiwi grape"}, {"item3": "mango pineapple"}]


@dataclass
class DefaultListDataclass:
    items: list[DefaultListItem] = field(default_factory=lambda: [])


async def simulate_stream_list_struct(
    interval_sec: float = 0.0,
) -> AsyncGenerator[str, None]:
    # Simulate a stream from a structured generator like OpenAI
    list_struct = DefaultListStruct(
        items=[
            DefaultListItem(item="apple &orange &straw&berry"),
            DefaultListItem(item="banana &kiwi &grape"),
            DefaultListItem(item="mango &pineapple"),
        ]
    )
    json_response = list_struct.model_dump_json()
    # we want to split on "{", ":", "," and " "
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


async def simulate_stream_openai(
    interval_sec: float = 0.0,
) -> AsyncGenerator[str, None]:
    response_tokens = [
        " ",
        '{"',
        "items",
        '":[',
        '{"',
        "item",
        '":"',
        "H",
        "ugg",
        "ing",
        " Face",
        " Transformers",
        ":",
        " A",
        " popular",
        " open",
        "-source",
        " library",
        " that",
        " provides",
        " a",
        " wide",
        " range",
        " etc...",
        '."',
        '},{"',
        "item",
        '":"',
        "L",
        "lama",
        ".cpp",
        ":",
        " A",
        " C",
        "++",
        " implementation",
        " for",
        " running",
        " L",
        "La",
        "MA",
        " and",
        " other",
        " large",
        " language",
        " etc...",
        '."',
        "}",
        "]}",
    ]

    for item in response_tokens:
        await asyncio.sleep(interval_sec)
        yield item
