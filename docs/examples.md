# Streaming Examples
Any library that supports structured streaming outputs should work with the `struct-strm` library. However, these use cases aren't widely doumented yet, so I'll add examples here for integrations. 

## OpenAI

First we can use the async OpenAI client with a structure to create a stream. Examples of creating the async stream with the OpenAI client can also be found in the [OpenAI docs](https://github.com/openai/openai-python).  
```python
from openai import AsyncOpenAI
from pydantic import BaseModel

client = AsyncOpenAI(api_key="your token here")

# Setup up all of the required info for the query
class DefaultListItem(BaseModel):
    item: str = ""

class DefaultListStruct(BaseModel):
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
class TestPerson(BaseModel):
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

## Ollama (Working Example - Dataclass)
This section provides a robust, working example demonstrating how to use `struct-strm` with a local Ollama server running its OpenAI-compatible API, using native **Python Dataclasses**. This approach resolves common compatibility issues by manually extracting the raw text tokens from the Ollama stream and using the generic `parse_hf_stream` wrapper.

```python
"""
------------------------------------------------------------
Ollama + Llama 3 Setup (Docker)
------------------------------------------------------------
Run the following commands before starting this script:

docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
docker exec -it ollama bash
ollama pull llama3

Notes:
- Models persist via the "ollama" volume.
- Ollama API runs at http://localhost:11434.
- Replace "llama3" with another model if needed.
------------------------------------------------------------
"""

from dataclasses import dataclass, field
import asyncio
from openai import AsyncOpenAI
from struct_strm import parse_hf_stream 
import sys
import json
from typing import AsyncGenerator

# --- Configuration & Client Setup ---

client = AsyncOpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
MODEL_NAME = "llama3"
QUERY = "Create a list describing 5 open source LLM tools"

# --- Dataclass Schema ---

@dataclass
class ToolItem:
    name: str = field(default="")
    description: str = field(default="")

@dataclass
class ToolList:
    tools: list[ToolItem] = field(default_factory=list)

# --- Schema & Example Setup ---

def create_few_shot_json() -> str:
    example_instance = ToolList(
        tools=[
            ToolItem(
                name="Hugging Face Transformers", 
                description="The industry-standard Python library providing thousands of pre-trained models for NLP, Vision, and Audio tasks, along with simple APIs for loading and using them."
            ),
            ToolItem(
                name="llama.cpp", 
                description="A high-performance C/C++ inference engine for Llama and other models, optimized for local CPU and efficient GPU execution, often used for running models on consumer hardware."
            )
        ]
    )
    
    example_dict = {"tools": [{"name": item.name, "description": item.description} for item in example_instance.tools]}
    return json.dumps(example_dict, indent=2)

def create_json_schema_prompt() -> str:
    return json.dumps({
        "type": "object",
        "properties": {
            "tools": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "The name of the open source tool."},
                        "description": {"type": "string", "description": "A brief description of the tool."},
                    }
                }
            }
        }
    }, indent=2)

# --- Stream Processing ---

async def extract_text_from_openai_stream(stream) -> AsyncGenerator[str, None]:
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

# --- Main Execution ---

async def main():
    few_shot_example_json = create_few_shot_json()
    json_schema_prompt = create_json_schema_prompt()
    
    print(f"Connecting to Ollama using model: {MODEL_NAME}")
    print(f"Query: {QUERY}\n")
    
    messages = [
        {"role": "system", "content": f"You are a helpful assistant that returns ONLY a JSON object based on the following schema instruction and example. SCHEMA: {json_schema_prompt} EXAMPLE: {few_shot_example_json}"},
        {"role": "user", "content": QUERY},
    ]

    try:
        openai_chunk_stream = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            response_format={"type": "json_object"}, 
            stream=True,
        )
    except Exception as e:
        print(f"\n--- Connection Error (during stream initiation) ---")
        print(f"Failed to create stream: {e}")
        print(f"Please ensure Ollama is running and model '{MODEL_NAME}' is available.")
        return

    raw_text_stream = extract_text_from_openai_stream(openai_chunk_stream)
    structured_updates_source = parse_hf_stream(raw_text_stream, ToolList) 

    print("--- Streaming Structured Output ---")
    
    async for generator_wrapper in structured_updates_source: 
        async for update in generator_wrapper:
            try:
                print("\n" + "=" * 50)
                print(f"| Update: {len(update.tools)} Tool(s) Parsed So Far") 
                print("=" * 50)
                
                for i, raw_data in enumerate(update.tools):
                    
                    if isinstance(raw_data, dict):
                        tool = ToolItem(**dict(raw_data))
                    else:
                        tool = raw_data

                    name_status = tool.name if hasattr(tool, 'name') and tool.name else "(parsing name...)"
                    desc_status = tool.description if hasattr(tool, 'description') and tool.description else "(parsing description...)"
                    
                    print(f"| Tool {i+1} Name: {name_status}")
                    print(f"| Tool {i+1} Desc: {desc_status}")
                    
            except Exception as e:
                print("\n--- CRITICAL DIAGNOSTIC ERROR (Final Check) ---")
                print(f"Error occurred while processing item {i}: {e}")
                print(f"Type of object that failed: {type(raw_data)}")
                print(f"The parent object was: {type(update)}")
                return 
            
    print("\n--- Stream Complete ---")

# --- Application Entrypoint ---

if __name__ == "__main__":
    if 'struct_strm' not in sys.modules:
        print("Error: The 'struct_strm' library is required. Please install it with 'pip install struct-strm'")
    else:
        try:
            asyncio.run(main())
        except Exception as e:
            print(f"\n--- An unexpected system error occurred ---")
            print(f"Error: {e}")
```

When the script runs, the ToolList dataclass is updated incrementally, demonstrating real-time structured parsing.
```bash
Connecting to Ollama using model: llama3
Query: Create a list describing 5 open source LLM tools

--- Streaming Structured Output ---

==================================================
| Update: 0 Tool(s) Parsed So Far
==================================================
.
.
==================================================
| Update: 1 Tool(s) Parsed So Far
==================================================
| Tool 1 Name: (parsing name...)
| Tool 1 Desc: (parsing description...)

==================================================
| Update: 1 Tool(s) Parsed So Far
==================================================
| Tool 1 Name: H
| Tool 1 Desc: (parsing description...)

==================================================
| Update: 1 Tool(s) Parsed So Far
==================================================
| Tool 1 Name: Hugging
| Tool 1 Desc: (parsing description...)

==================================================
| Update: 1 Tool(s) Parsed So Far
==================================================
| Tool 1 Name: Hugging Face
| Tool 1 Desc: (parsing description...)

==================================================
| Update: 1 Tool(s) Parsed So Far
==================================================
| Tool 1 Name: Hugging Face Transformers
| Tool 1 Desc: (parsing description...)
.
.
==================================================
| Update: 5 Tool(s) Parsed So Far
==================================================
| Tool 1 Name: Hugging Face Transformers
| Tool 1 Desc: The industry-standard Python library providing thousands of pre-trained models for NLP, Vision, and Audio tasks, along with simple APIs for loading and using them.
| Tool 2 Name: llama.cpp
| Tool 2 Desc: A high-performance C/C++ inference engine for Llama and other models, optimized for local CPU and efficient GPU execution, often used for running models on consumer hardware.
| Tool 3 Name: Optimus
| Tool 3 Desc: An open-source Python library that generates natural language text based on a prompt using various AI algorithms, allowing developers to build robust language models and conversational interfaces.
| Tool 4 Name: Rasa
| Tool 4 Desc: A popular open-source natural language processing framework for building contextual chatbots and conversational interfaces, focused on integrating NLP with machine learning and business logic.
| Tool 5 Name: Stanford CoreNLP
| Tool 5 Desc: A robust Java library that leverages the power of machine learning models to perform various NLP tasks, such as tokenization, part-of-speech tagging, named entity recognition, and sentiment analysis.
--- Stream Complete ---
```