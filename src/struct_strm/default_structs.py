from typing import List, Generator, Dict, Union
from pydantic import BaseModel

def get_struct_keys(struct: BaseModel) -> List[str]:
    return list(struct.model_fields.keys())

class DefaultListItem(BaseModel):
    item: str

class DefaultListStruct(BaseModel):
    # mostly just for testing
    items: List[DefaultListItem]
    # ex: itesms=[{"item": "apple orange"}, {"item2": "banana kiwi grape"}, {"item3": "mango pineapple"}]

def simulate_stream_list_struct() -> Generator[str, None, None]:       
    # Simulate a stream from a structured generator like OpenAI
    list_struct = DefaultListStruct(items=[
        DefaultListItem(item="apple &orange"), 
        DefaultListItem(item="banana &kiwi &grape"), 
        DefaultListItem(item="mango &pineapple")
    ])
    json_response = list_struct.model_dump_json() 
    # we want to split on "{", ":", "," and " "
    json_response = json_response.replace("{", " { ").replace(":", " : ").replace(",", " , ").replace("}", " } ")
    stream_response = json_response.split(" ")
    for item in stream_response:
        item = item.replace("&", " ")
        yield item

