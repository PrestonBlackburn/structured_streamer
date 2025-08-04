import time
import csv
from struct_strm import (
    parse_openai_stream, 
    aget_openai_client,
)

from  struct_strm.structs.list_structs import DefaultListStruct, DefaultListItem
from typing import Type, AsyncGenerator

# List example with openai
import logging

_logger = logging.getLogger(__name__)


# async def simple_benchmark_struct_strm(n=10):


# async def simple_benchmark_vanilla(n=10):


async def static_list_benchmark(client, model, messages, TestStruct):
    # test values
    time_first_token = 0
    time_first_meaningful_chunk = 0
    time_last_chunk = 0

    start = time.time()

    completion =  await client.chat.completions.parse(
        model=model,
        messages=messages,
        response_format=TestStruct,
        temperature=0.0,
    )
    time_first_token = time.time() - start
    time_first_meaningful_chunk = time.time() - start
    time_last_chunk = time.time() - start
    # list_object_response = completion.choices[0].message

    print("--------- Static Test Results ------------")
    print(f"Time to first token: {time_first_token} seconds")
    print(f"Time to first meaningful chunk: {time_first_meaningful_chunk} seconds")
    print(f"Time to last chunk: {time_last_chunk} seconds")

    return time_first_token, time_first_meaningful_chunk, time_last_chunk

async def stream_list_benchmark(client, model, messages, TestStruct):
    # test values
    time_first_token = 0
    time_first_meaningful_chunk = 0
    time_last_chunk = 0

    start = time.time()
    # we need to strip out the initial "{'response': " json that gets returned
    stream =  client.beta.chat.completions.stream(
        model=model,
        messages=messages,
        response_format=TestStruct,
        temperature=0.0,
    )

    structured_response_stream = parse_openai_stream(stream, TestStruct)
    async for structure in structured_response_stream:
        async for list_struct in structure:
            if time_first_token == 0:
                time_first_token = time.time() - start
            if list_struct.items and time_first_meaningful_chunk == 0:
                time_first_meaningful_chunk = time.time() - start
    time_last_chunk = time.time() - start

    print("--------- Streamed Test Results ------------")
    print(f"Time to first token: {time_first_token} seconds")
    print(f"Time to first meaningful chunk: {time_first_meaningful_chunk} seconds")
    print(f"Time to last chunk: {time_last_chunk} seconds")

    return time_first_token, time_first_meaningful_chunk, time_last_chunk

async def list_benchmark(n:int=1, save:bool = True):
    # parameters
    TestStruct = DefaultListStruct
    few_shot_examples = DefaultListStruct(
        items=[
            DefaultListItem(item="The Hugging Face Transformers library is an open-source Python library that provides access to a vast collection of pre-trained Transformer models for various machine learning tasks. While initially focused on Natural Language Processing (NLP), its capabilities have expanded to include computer vision, audio processing, and multimodal applications.")
        ]
    ).model_dump_json()
    prompt_context = ""
    query = "Create list describing 10 open source llm tools"
    model = "gpt-4.1-mini"

    client = await aget_openai_client()
    messages = []
    messages.append({"role": "system", "content": prompt_context})
    if few_shot_examples is not None:
        messages.append({"role": "system", "content": f"example response: {few_shot_examples}"})
    messages.append({"role": "user", "content": query})


    results = [("ttft_stream", "ttfmc_stream", "ttlc_stream", "ttft_static", "ttfmc_static", "ttlc_static")]
    for i in range(n):
        ttft_static, ttfmc_static, ttlc_static = await static_list_benchmark(client, model, messages, TestStruct)
        ttft_stream, ttfmc_stream, ttlc_stream = await stream_list_benchmark(client, model, messages, TestStruct)

        results.append((ttft_static, ttfmc_static, ttlc_static , ttft_stream, ttfmc_stream, ttlc_stream))
        time.sleep(5)


    if save:
        with open('tests/benchmarks/list_gen_benchmark.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            
            writer.writerows(results)

    return ttft_stream, ttfmc_stream, ttlc_stream, ttft_static, ttfmc_static, ttlc_static


def create_benchmark_chart():
    ...



if __name__ == "__main__":
    import asyncio
    _logger.setLevel(logging.INFO)
    asyncio.run(list_benchmark(n = 10))

    # open q's - what do we consider a meaningful chunk?