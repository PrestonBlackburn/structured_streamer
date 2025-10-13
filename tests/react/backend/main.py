from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json

app = FastAPI()

# Allow all origins for this small local example so the frontend
# served from a simple static server can access the stream.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

async def ndjson_stream():
    for i in range(1, 6):
        obj = {"id": i, "value": f"Item {i}"}
        yield json.dumps(obj) + "\n"
        await asyncio.sleep(0.4)

@app.get("/stream")
async def stream():
    return StreamingResponse(ndjson_stream(), media_type="application/x-ndjson")
