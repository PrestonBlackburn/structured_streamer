# Streaming Examples
Any library that supports structured streaming outputs should work with the `struct-strm` library. However, these use cases aren't widely doumented yet, so I'll add examples here for integrations. 

## OpenAI

First we can use the async OpenAI client with a structure to create a stream. Examples of creating the async stream with the OpenAI client can also be found in the [OpenAI docs](https://github.com/openai/openai-python).  
```python
from openai import AsyncOpenAI
from pydantic import BaseModel

client = AsyncOpenAI(api_key="your token here")

# Setup up all of the required info for the query
class PydanticDefaultListItem(BaseModel):
    item: str = ""

class PydanticDefaultListStruct(BaseModel):
    # mostly just for testing
    items: list[DefaultListItem] = []

# The few shot example is optional
few_shot_examples = DefaultListStruct(
    items=[
        DefaultListItem(item="The Hugging Face Transformers library is an open-source Python library that provides access to a vast collection of pre-trained Transformer models for various machine learning tasks. While initially focused on Natural Language Processing (NLP), its capabilities have expanded to include computer vision, audio processing, and multimodal applications.")
    ]
).model_dump_json()
query = "Create list describing 10 open source llm tools"
model = "gpt-4.1-mini"


# create the messages - 
messages = []
messages.append({"role": "system", "content": f"example response: {few_shot_examples}"})
messages.append({"role": "user", "content": query})

stream =  await client.chat.completions.parse(
    model=model,
    messages=messages,
    response_format=DefaultListStruct,
    temperature=0.0,
)
```

Now that we have the OpenAI completion stream we can wrap it using the `struct-strm` library to return structures instead of strings. 
```python
from struct_strm import parse_openai_stream 
import asyncio

# you'll want to use a function to handle the async generator
async def your_streamed_response_function(stream, DefaultListStruct):
    structured_response_stream = parse_openai_stream(stream, DefaultListStruct)
    async for structure in structured_response_stream:
        async for list_struct in structure:
            # do whatever you want with these results
            print(list_struct)

# you would probably do something with this function,
# but we'll just run it for example purposes
asyncio.run(your_streamed_response_function(stream, DefaultListStruct))
```

Fully formed python classes are returned:
```bash
>>>  DefaultListStruct(items=[DefaultListItem(item="")])
>>>  DefaultListStruct(items=[DefaultListItem(item="Pytorch")])
>>>  DefaultListStruct(items=[DefaultListItem(item="Pytorch is")])
>>>  etc....
```

## Hugging Face

For an open source approach, we can use Hugging Face (or other libraries) and XGrammar. XGrammar is an open-source library for efficient, flexible, and portable structured generation. XGrammar is an open-source library for efficient, flexible, and portable structured generation. You can read more about XGrammar [here](https://xgrammar.mlc.ai/), but I'll assume you have already read the docs for this example.   

<br/>

There is a bit of setup we need to do, since we will modify the logits of a foundation model to enable the grammar constrained decoding that matches our provided Pydantic (or json) schema.  

<br/>

First we'll import everything that we'll need and setup the initial model configs.
```python
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
```

The bulk of the logic is in this next section. Again, most of this is outlined in the XGrammar docs, but basically we need to: 
- Create a compiled grammar based on our target structure with our model's tokenizer + XGrammar
- Create a logits processor based on the grammar to filter the response tokens to our specified grammar
- Start a new thread to support streaming the hugging face model response

```python
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
```

Finally we can take the stream generated by the model + xgrammar and pass it to the `struct-strm` hugging face wrapper.

```python
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


# run the example
class PydanticTestPerson(BaseModel):
    name: str = ""
    age: str = ""

user_query = "Introduce yourself in JSON with two fields: name and age."

asyncio.run(test_hf_stream(user_query, TestPerson))
```

Fully formed python classes are returned:
```bash
>>>  TestPerson(name="", age="")
>>>  TestPerson(name="bilbo", age="")
>>>  TestPerson(name="bilbo baggins", age="")
>>>  TestPerson(name="bilbo baggins", age="111")
```