import os
from functools import lru_cache


@lru_cache(maxsize=1)
def get_openai_env():
    api_key = os.environ.get("OPENAI_API_KEY", None)
    openai_params = {
        "api_key": api_key,
    }
    return openai_params
