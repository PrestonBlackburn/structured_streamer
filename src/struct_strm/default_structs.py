from typing import List, Generator, Dict
from pydantic import BaseModel


class ListStruct(BaseModel):
    # mostly just for testing
    items: List[Dict[str, str]]
    # ex: itesms=[{"item": "apple orange"}, {"item2": "banana kiwi grape"}, {"item3": "mango pineapple"}]

def simulate_stream_list_struct() -> Generator[str, None, None]:       
    # Simulate a stream from a structured generator like OpenAI
    list_struct = ListStruct(items=[
        {"item": "apple &orange"}, 
        {"item": "banana &kiwi &grape"}, 
        {"item": "mango &pineapple"}
    ])
    json_response = list_struct.model_dump_json() 
    # we want to split on "{", ":", "," and " "
    json_response = json_response.replace("{", " { ").replace(":", " : ").replace(",", " , ").replace("}", " } ")
    stream_response = json_response.split(" ")
    for item in stream_response:
        item = item.replace("&", " ")
        yield item

