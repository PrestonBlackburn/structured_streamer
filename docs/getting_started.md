# Installation

Install With Pypi:
```bash
pip install struct-strm
```

# Usage

This is an example of a simple case where we return a list from a structured llm output. Despite json strings being returned, `struct_strm` is able to return a streamable list as the response. 

```python
from struct_strm.llm_wrappers import openai_stream_wrapper
from struct_strm.structs.list_structs import DefaultListStruct

# The query and context for the LLM call
prompt_context = ""
user_query = "Create list describing 5 open source llm tools"

class DefaultListItem(BaseModel):
    item: str = ""

class DefaultListStruct(BaseModel):
    # mostly just for testing
    items: list[DefaultListItem] = []

# We can return the json stream from openai
# *support for more llms in the future
stream = openai_stream_wrapper(
    user_query,
    prompt_context,
    DefaultListStruct,
)

# Now we can parse the json stream from OpenAI.
# This creates our incremental output structure, a list, in this case
import asyncio
from struct_strm import parse_list_json
from struct_strm.structs.list_structs import (
    simulate_stream_list_struct,
    simulate_stream_openai,
)

async def test_list_parse(stream):
    async for items in parse_list_json(stream):
        print(items)

asyncio.run(test_list_parse(stream))

```

As we loop through the items in the async for loop:  

```markdown
>>> DefaultListStruct(items=[DefaultListItem(item="Hugg")])
>>> DefaultListStruct(items=[DefaultListItem(item="Hugging")])
>>> DefaultListStruct(items=[DefaultListItem(item="Hugging Face")])
>>> DefaultListStruct(items=[DefaultListItem(item="Hugging Face Trans")])
>>> DefaultListStruct(items=[DefaultListItem(item="Hugging Face Transformers")])
>>> DefaultListStruct(items=[DefaultListItem(item="Hugging Face Transformers:")])
>>> etc...
>>> DefaultListStruct(items=[DefaultListItem(item="Hugging Face Transformers: A popular open-source library etc....")])
>>> DefaultListStruct(items=[DefaultListItem(item="Hugging Face Transformers: A popular open-source library etc...."), DefaultListItem(item="Llama")])
>>> DefaultListStruct(items=[DefaultListItem(item="Hugging Face Transformers: A popular open-source library etc...."), DefaultListItem(item="Llama.")])
>>> DefaultListStruct(items=[DefaultListItem(item="Hugging Face Transformers: A popular open-source library etc...."), DefaultListItem(item="Llama.cpp")])
>>> DefaultListStruct(items=[DefaultListItem(item="Hugging Face Transformers: A popular open-source library etc...."), DefaultListItem(item="Llama.cpp:")])
>>> DefaultListStruct(items=[DefaultListItem(item="Hugging Face Transformers: A popular open-source library etc...."), DefaultListItem(item="Llama.cpp: A")])
>>> etc...
```

## HTML Components
This library also provides some convience functions for serving html components (htmx style and vanilla javascript) direclty to the frontend. Reference implementations can be found in the `tests/02_app` directory. If you use frontend frameworks like React, you can ignore this section and directly use the core library.   

<br/>

Since we are streaming structured outputs for the purpose of using them in the UI, we know we need several features, such as a pre-response placeholder, streaming reading/updates, and a final post response indicator. Right now I have some minimal implementations included in this library. They are not super customizable yet, but can serve as references for your projects.

<br/>  


![Example Form Streaming](img/form_struct_strm.gif)

<br/>  

Example usage with FastAPI and HTMX:
```python
from struct_strm.structs.list_structs import DefaultListStruct
from struct_strm.ui_components import ListComponent
from struct_strm.structs.list_structs import simulate_stream_list_struct

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()

templates = Jinja2Templates(directory="tests/app")

@app.get("/get_list_stream")
def test_fetch_list_sse():
    # kick off SSE stream
    sse_container = "sse-list"
    stream_target = "stream-list"
    component_path = "/test_list"
    sse_html = f"""<div 
         id="sse-list-container"
         hx-ext="sse"
         sse-connect="{component_path}">
            <div 
                sse-swap="message" 
                hx-target="#{stream_target}" 
                hx-swap="innerHTML">
            </div>
            <div
                sse-swap="streamCompleted" 
                hx-target="#{sse_container}">
            </div>
        </div>
    """
    return HTMLResponse(content=sse_html, media_type="text/html")


@app.get("/test_list")
async def test_list():

    component = ListComponent()
    stream: AsyncGenerator = simulate_stream_list_struct(interval_sec=0.02)
    html_component_stream: AsyncGenerator = component.render(response_stream=stream)

    async def wrapper():
        async for item in html_component_stream:
            print(item)
            yield item
        yield {"event": "streamCompleted", "data": ""}

    return EventSourceResponse(wrapper(), media_type="text/event-stream")

```
