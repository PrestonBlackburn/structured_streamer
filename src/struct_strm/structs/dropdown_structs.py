import asyncio
from typing import List, AsyncGenerator
from pydantic import BaseModel
from dataclasses import dataclass, field
from struct_strm.compat import to_json


class DropdownOption(BaseModel):
    value: str = ""
    label: str = ""


class DefaultDropdown(BaseModel):
    # L1 fields (use distinct key names from nested structs to avoid query collisions)
    dropdown_label: str = "Select an option"
    selected: str = ""
    # L2 list of string-field structs
    options: List[DropdownOption] = []


@dataclass
class DataclassDropdownOption:
    value: str = ""
    label: str = ""


@dataclass
class DataclassDefaultDropdown:
    label: str = "Select an option"
    selected: str = ""
    options: list[DataclassDropdownOption] = field(default_factory=lambda: [])


async def simulate_stream_dropdown(
    interval_sec: float = 0.0, struct_type: str = "pydantic"
) -> AsyncGenerator[str, None]:

    if struct_type == "pydantic":
        dd = DefaultDropdown(
            dropdown_label="Select an option",
            selected="opt_b",
            options=[
                DropdownOption(value="opt_a", label="Option A"),
                DropdownOption(value="opt_b", label="Option B"),
                DropdownOption(value="opt_c", label="Option C"),
            ],
        )
    elif struct_type == "dataclass":
        dd = DataclassDefaultDropdown(
            label="Select an option",
            selected="opt_b",
            options=[
                DataclassDropdownOption(value="opt_a", label="Option A"),
                DataclassDropdownOption(value="opt_b", label="Option B"),
            ],
        )
    else:
        raise ValueError(f"Invalid struct type: {struct_type}")

    json_response = to_json(dd)
    json_response = (
        json_response.replace("{", "&{&")
        .replace(":", "&:&")
        .replace(",", "&,&")
        .replace("}", "&}&")
    )
    for item in json_response.split("&"):
        yield item.replace("&", "")
        await asyncio.sleep(interval_sec)


async def simulate_stream_dropdown_openai(
    interval_sec: float = 0.0,
) -> AsyncGenerator[str, None]:

    tokens = [
        " ",
        '{"',
        "dropdown_label",
        '":"',
        "Select",
        " an",
        " option",
        '"',
        ", ",
        '"',
        "selected",
        '":"',
        "opt_b",
        '"',
        ", ",
        '"',
        "options",
        '":[',
        '{"',
        "value",
        '":"',
        "opt_a",
        '"',
        ", ",
        '"',
        "label",
        '":"',
        "Option",
        " A",
        '"',
        "}",
        ", ",
        '{"',
        "value",
        '":"',
        "opt_b",
        '"',
        ", ",
        '"',
        "label",
        '":"',
        "Option",
        " B",
        '"',
        "}",
        "]",
        "}",
    ]
    for t in tokens:
        await asyncio.sleep(interval_sec)
        yield t


