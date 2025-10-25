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