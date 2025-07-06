from functools import lru_cache
from struct_strm.env import get_openai_env
from openai import AsyncOpenAI
from tiktoken import get_encoding, Encoding


async def aget_openai_client() -> AsyncOpenAI:
    params = get_openai_env()
    client = AsyncOpenAI(api_key=params["api_key"])
    return client


@lru_cache(maxsize=1)
def get_openai_token_encoding(encoder: str = "cl100k_base") -> Encoding:
    encoding = get_encoding(encoder)
    return encoding


async def count_openai_tokens(text: str, encoder: str = "cl100k_base") -> int:
    encoding = get_openai_token_encoding(encoder=encoder)
    num_tokens = len(encoding.encode(text))
    return num_tokens
