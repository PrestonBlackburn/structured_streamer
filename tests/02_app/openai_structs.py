from struct_strm.llm_clients import aget_openai_client
from typing import List, Union, Callable, AsyncGenerator, Dict, Type
from openai.types.chat import ParsedChatCompletion

# List example with openai


async def openai_structured_streamer(
    user_query: str,
    prompt_context: str,
    ResponseFormat: Type,
    few_shot_examples: List[Dict[str, str]] = None,
) -> AsyncGenerator:
    # we may need to handle
    client = await aget_openai_client()
    messages = []
    messages.append({"role": "system", "content": prompt_context})
    messages.extend(few_shot_examples)
    messages.append({"role": "user", "content": user_query})

    async with client.beta.chat.completions.stream(
        model="gpt-4.1",
        messages=messages,
        response_format=ResponseFormat,
        temperature=0.0,
    ) as stream:
        async for event in stream:
            if event.type == "content.delta":
                delta = event.delta
                yield delta
            elif event.type == "content.done":
                pass
                # print("content.done")
            elif event.type == "error":
                print("Error in stream:", event.error)
