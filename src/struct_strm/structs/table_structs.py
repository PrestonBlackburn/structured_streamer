import asyncio
import time
from typing import List, AsyncGenerator
from pydantic import BaseModel


class ExampleRow(BaseModel):
    title: str = ""
    genre: str = ""
    rating: str = ""


class ExampleTableStruct(BaseModel):
    # mostly just for testing
    table: List[ExampleRow] = []
    # ex: table =  [
    #     {"title": "Akira", "genre": "action, cyberpunk, horror", "rating": "5"},
    #     {"title": "2001: A Space Odyssey", "genre": "Sci-fi, Suspense", "rating": "5"},
    #     {"title": "Gattaca", "genre": "Sci-fi, Thriller", "rating": "4"},
    #  ]


async def simulate_stream_table_struct(
    interval_sec: float = 0.0,
) -> AsyncGenerator[str, None]:
    # Simulate a stream from a structured generator like OpenAI
    list_struct = ExampleTableStruct(
        table=[
            ExampleRow(title="Akira", genre="action, &cyberpunk, &horror", rating="5"),
            ExampleRow(
                title="2001: A &Space Odyssey", genre="Sci-fi, &Suspense", rating="5"
            ),
            ExampleRow(title="Gattaca", genre="Sci-fi, &Thriller", rating="4"),
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


async def simulate_stream_table_openai(
    interval_sec: float = 0.0,
) -> AsyncGenerator[str, None]:
    response_tokens = [
        " ",
        '{"',
        "table",
        '":[',
        '{"',
        "title",
        '":"',
        "Akira",
        '"',
        ", ",
        '"',
        "genre",
        '":"',
        "action",
        ",",
        " cyberpunk",
        ",",
        " horror",
        '."',
        ", ",
        '"',
        "rating",
        '":"',
        "5",
        '"',
        '},{"',
        "title",
        '":"',
        "2001: ",
        "A",
        " Space",
        " Odyssey",
        '"',
        ", ",
        '"',
        "genre",
        '":"',
        "Sci-",
        "fi",
        ",",
        " Suspense",
        '."',
        ", ",
        '"',
        "rating",
        '":"',
        "5",
        '"',
        "}",
        "]}",
    ]

    for item in response_tokens:
        await asyncio.sleep(interval_sec)
        yield item
