
from threading import Thread
from typing import Generator, AsyncGenerator
import asyncio
import torch
from transformers import (
    AutoTokenizer,
    AutoConfig,
    AutoModelForCausalLM,
)
import xgrammar as xgr
from transformers import AsyncTextIteratorStreamer
from pydantic import BaseModel

from struct_strm.llm_wrappers import parse_hf_stream

def init_model():
    device = 'cpu'
    # tokenizer info:
    model_name = "deepseek-ai/deepseek-coder-1.3b-instruct"
    model = AutoModelForCausalLM.from_pretrained(
            model_name, torch_dtype=torch.float32, device_map=device
    )
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    config = AutoConfig.from_pretrained(model_name)

    return model, tokenizer, config


async def test_async_query(user_query: str, Schema: BaseModel) -> AsyncGenerator[str, None]:
    model, tokenizer, config = init_model()

    messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_query}
    ]

    text = tokenizer.apply_chat_template(
        messages, 
        tokenize=False,
        add_generation_prompt=True
    )

    model_inputs = tokenizer(
        text,
        return_tensors="pt",
    ).to(model.device)

    full_vocab_size = config.vocab_size
    tokenizer_info = xgr.TokenizerInfo.from_huggingface(
        tokenizer,
        vocab_size=full_vocab_size,
    )
    compiler = xgr.GrammarCompiler(tokenizer_info)

    compiled_grammar = compiler.compile_json_schema(Schema)
    xgr_logits_processor = xgr.contrib.hf.LogitsProcessor(compiled_grammar)

    async_streamer = AsyncTextIteratorStreamer(
        tokenizer, 
        timeout=60.0,
        skip_prompt=True, 
        skip_special_tokens=True
    )
    generation_kwargs = dict(
        **model_inputs,
        max_new_tokens=20,
        logits_processor=[xgr_logits_processor],
        streamer = async_streamer,
    )
    thread = Thread(target = model.generate, kwargs=generation_kwargs)
    thread.start()
    try:
        async for token in async_streamer:
            yield token
    finally:
        thread.join() 


async def test_hf_stream(
    user_query: str, 
    Schema: BaseModel
) -> AsyncGenerator[BaseModel, None]:
    """
    Test the Hugging Face stream with a given user query and schema.
    """
    stream = test_async_query(user_query, Schema)
    structured_response_stream = parse_hf_stream(stream, Schema)
    async for structure in structured_response_stream:
        async for schema_struct in structure:
            print(f"Struct: {type(schema_struct)} - {schema_struct}")

if __name__ == "__main__":
    
    class PydanticTestPerson(BaseModel):
        name: str = ""
        age: str = ""

    user_query = "Introduce yourself in JSON with two fields: name and age."

    asyncio.run(test_hf_stream(user_query, TestPerson))