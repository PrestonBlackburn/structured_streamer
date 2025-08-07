from functools import lru_cache
import os
try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

@lru_cache(maxsize=1)
def get_openai_env():
    api_key = os.environ.get("OPENAI_API_KEY", None)
    openai_params = {
        "api_key": api_key,
    }
    return openai_params


async def aget_openai_client() -> AsyncOpenAI:
    if AsyncOpenAI is None:
        raise ImportError("OpenAI library is not available. Please install struct-strm with the openai option - pip install struct-strm[openai].")
    params = get_openai_env()
    client = AsyncOpenAI(api_key=params["api_key"])
    return client
