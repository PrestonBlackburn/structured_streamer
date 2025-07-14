from typing import AsyncGenerator
import asyncio
from pydantic import BaseModel

from struct_strm.llm_wrappers import openai_stream_wrapper
from struct_strm.structs.list_structs import DefaultListItem, DefaultListStruct

from struct_strm.ui_components import ListComponent, FormComponent
from struct_strm.structs.list_structs import simulate_stream_list_struct
from struct_strm.structs.form_structs import (
    simulate_stream_form_struct,
    simulate_stream_form_openai,
)

from fastapi import FastAPI, Request, status
from fastapi.responses import StreamingResponse, HTMLResponse
from sse_starlette.sse import EventSourceResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()

templates = Jinja2Templates(directory="tests/app")


@app.get("/")
async def home(request: Request) -> HTMLResponse:
    context = {"request": request}
    # later - contextually show landing page stuff
    response = templates.TemplateResponse("test_webpage.html", context)
    return response


class HealthCheck(BaseModel):
    status: str = "OK"


@app.get("/health", status_code=status.HTTP_200_OK, response_model=HealthCheck)
async def health_check() -> HealthCheck:
    return HealthCheck()


# ---------------------------------------------------
# --------------- The Very Basic Tests -----------------
# ---------------------------------------------------
async def test_gen() -> AsyncGenerator:
    for i in range(5):
        yield f"""<div> Item {i} </div>"""
        await asyncio.sleep(0.25)


@app.get("/get_test_stream")
async def get_test_minimal_sse():
    # kick off SSE stream
    sse_container = "sse"
    stream_target = "stream-content"
    component_path = "/test_stream"
    sse_html = f"""<div 
         id="sse-container"
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


@app.get("/test_stream")
async def test_minimal():
    async def event_test_gen():
        stream = test_gen()
        async for item in stream:
            yield item
        yield {"event": "streamCompleted", "data": ""}

    return EventSourceResponse(event_test_gen(), media_type="text/event-stream")


@app.get("/test_incremental")
async def test_incremental():

    return StreamingResponse(test_gen(), media_type="text/html")


# ---------------------------------------------------
# ------------- Test The List Component -----------------
# ---------------------------------------------------
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
    # return  StreamingResponse(html_component_stream, media_type="text/html")


# ---------------------------------------------------
# ------------ Test With OpenAI Integration -------------
# ---------------------------------------------------


@app.get("/get_openai_test_stream")
def test_fetch_list_openai_sse():
    # kick off SSE stream
    sse_container = "sse-openai-list"
    stream_target = "stream-openai-list"
    component_path = "/test_openai_list"
    sse_html = f"""<div 
         id="sse-openai-list-container"
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


@app.get("/test_openai_list")
async def test_openai_list():
    component = ListComponent()

    prompt_context = ""
    user_query = "Create list describing 5 open source llm tools"

    stream: AsyncGenerator = openai_stream_wrapper(
        user_query,
        prompt_context,
        DefaultListStruct,
    )

    html_component_stream: AsyncGenerator = component.render(response_stream=stream)
    print("starting openai stream")

    async def wrapper():
        async for item in html_component_stream:
            # print(item)
            yield item

        yield {"event": "streamCompleted", "data": ""}

    return EventSourceResponse(wrapper(), media_type="text/event-stream")


# ----------------------------------------------------
# -------------------- Test Form ---------------------
# ----------------------------------------------------


@app.get("/get_form_stream")
def test_fetch_form_sse():
    # kick off SSE stream
    sse_container = "sse-form"
    stream_target = "stream-form"
    component_path = "/test_form"
    sse_html = f"""<div 
         id="sse-form-container"
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


@app.get("/test_form")
async def test_list():

    component = FormComponent()
    stream: AsyncGenerator = simulate_stream_form_struct(interval_sec=0.02)
    html_component_stream: AsyncGenerator = component.render(response_stream=stream)

    async def wrapper():
        async for item in html_component_stream:
            print(item)
            yield item
        yield {"event": "streamCompleted", "data": ""}

    return EventSourceResponse(wrapper(), media_type="text/event-stream")
    # return  StreamingResponse(html_component_stream, media_type="text/html")
