from struct_strm.llm_clients import aget_openai_client
from typing import List, Union, Callable, AsyncGenerator, Dict, Type
from openai.types.chat import ParsedChatCompletion
from dataclasses import field

# List example with openai
import logging

_logger = logging.getLogger(__name__)


async def openai_stream_wrapper(
    user_query: str,
    prompt_context: str,
    ResponseFormat: Type,
    few_shot_examples: List[Dict[str, str]] = None,
) -> AsyncGenerator:

    client = await aget_openai_client()
    messages = []
    messages.append({"role": "system", "content": prompt_context})
    if few_shot_examples is not None:
        messages.extend(few_shot_examples)
    messages.append({"role": "user", "content": user_query})

    # we need to strip out the initial "{'response': " json that gets returned
    async with client.beta.chat.completions.stream(
        model="gpt-4.1",
        messages=messages,
        response_format=ResponseFormat,
        temperature=0.0,
    ) as stream:
        async for event in stream:
            if event.type == "content.delta":
                delta = event.delta
                _logger.debug(f"Delta: {delta}")  # get tokens for better mocks
                yield delta
            elif event.type == "content.done":
                _logger.info("OpenAI stream complete")
                pass
            elif event.type == "error":
                _logger.error(f"Error in stream: {event.error}")
