import asyncio
from typing import List, AsyncGenerator
from pydantic import BaseModel
from dataclasses import dataclass, field
from struct_strm.compat import to_json


class DefaultFormItem(BaseModel):
    field_name: str = ""
    field_placeholder: str = ""


class DefaultFormStruct(BaseModel):
    # mostly just for testing
    form_fields: List[DefaultFormItem] = []
    # ex: form_fields=[{"field_name": "fruits", "field_placeholder": "apple orange"}, {"field_name": "appliance"}, {"item3": "mango pineapple"}]


@dataclass
class DataclassDefaultFormItem:
    field_name: str = ""
    field_placeholder: str = ""


@dataclass
class DataclassDefaultFormStruct:
    form_fields: List[DataclassDefaultFormItem] = field(default_factory=lambda: [])


async def simulate_stream_form_struct(
    interval_sec: float = 0.0, struct_type: str = "pydantic"
) -> AsyncGenerator[str, None]:
    # Simulate a stream from a structured generator like OpenAI
    if struct_type == "pydantic":
        list_struct = DefaultFormStruct(
            form_fields=[
                DefaultFormItem(
                    field_name="fruits", field_placeholder="apple &orange &straw&berry"
                ),
                DefaultFormItem(
                    field_name="appliance", field_placeholder="blender &mixer &toaster"
                ),
                DefaultFormItem(field_name="dishes", field_placeholder="plate &bowl"),
            ]
        )
    elif struct_type == "dataclass":
        list_struct = DataclassDefaultFormStruct(
            form_fields=[
                DataclassDefaultFormItem(
                    field_name="fruits", field_placeholder="apple &orange &straw&berry"
                ),
                DataclassDefaultFormItem(
                    field_name="appliance", field_placeholder="blender &mixer &toaster"
                ),
                DataclassDefaultFormItem(
                    field_name="dishes", field_placeholder="plate &bowl"
                ),
            ]
        )
    else:
        raise ValueError(f"Invalid struct type: {struct_type}")
    json_response = to_json(list_struct)
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


async def simulate_stream_form_openai(
    interval_sec: float = 0.0,
) -> AsyncGenerator[str, None]:
    response_tokens = [
        " ",
        '{"',
        "form_fields",
        '":[',
        '{"',
        "field_name",
        '":"',
        "fruits",
        '"',
        ", ",
        '"',
        "field_placeholder",
        '":"',
        "apple",
        " orange",
        " straw",
        "berry",
        '"',
        '},{"',
        "field_name",
        '":"',
        "appliance",
        '"',
        ", ",
        '"',
        "field_placeholder",
        '":"',
        "blender",
        " mixer",
        " toaster",
        '"',
        "}",
        "]}",
    ]

    for item in response_tokens:
        await asyncio.sleep(interval_sec)
        yield item
