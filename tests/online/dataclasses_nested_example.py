"""
------------------------------------------------------------
Ollama Setup (Docker)
------------------------------------------------------------
Run the following commands before starting this script:

docker run --rm -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
(or with gpu support: docker run --gpus all --rm -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama)
docker exec -it ollama bash
ollama pull llama3
------------------------------------------------------------
"""

from struct_strm import parse_hf_stream, to_json
from openai import AsyncOpenAI
from dataclasses import dataclass, field
import json
import logging
from typing import AsyncGenerator
import asyncio

_logger = logging.getLogger(__name__)

@dataclass
class Answer:
    answer_text: str = field(default="")
    is_correct: bool = field(default=False)

@dataclass
class Questions:
    question: str = field(default="")
    answers: list[Answer] = field(default_factory= list)

def create_few_shot_json() -> Questions:
    example_instance = Questions(
            question = "Which of the following are ML Libraries?",
            answers = [
                    Answer("Pytorch", True),
                    Answer("Microsoft Word", False),
                    Answer("Sklearn", True),
                    Answer("Kubernetes", False)
            ]
        )
    
    return example_instance

def create_json_schema_prompt() -> str:
    # would be nice to just auto-generate this
    return json.dumps(
{
  "type": "object",
  "title": "Questions",
  "description": "A container for a single quiz question and all its possible answers.",
  "properties": {
    "question": {
      "type": "string",
      "description": "The text of the question itself (e.g., 'Which of the following are ML Libraries?').",
      "default": ""
    },
    "answers": {
      "type": "array",
      "description": "A list of possible answers for the question.",
      "items": {
        "type": "object",
        "title": "Answer",
        "properties": {
          "answer_text": {
            "type": "string",
            "description": "The text of the potential answer.",
            "default": ""
          },
          "is_correct": {
            "type": "boolean",
            "description": "Indicates if this answer is the correct one.",
            "default": False
          }
        },
        "required": ["answer_text", "is_correct"],
        "additionalProperties": False
      },
      "default": []
    }
  },
  "required": ["question", "answers"],
  "additionalProperties": False
}, indent=2)

async def extract_text_from_stream(stream) -> AsyncGenerator[str, None]:
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

async def main(client: AsyncOpenAI, messages: list):
    _logger = logging.getLogger(__name__)

    chunk_stream = await client.chat.completions.create(
        model = MODEL_NAME,
        messages = messages,
        response_format = {"type": "json_object"},
        stream = True
        )

    raw_text_stream = extract_text_from_stream(chunk_stream)
    structured_response_stream = parse_hf_stream(raw_text_stream, Questions)

    _logger.info("---- Streaming Output -----")
    async for structure in structured_response_stream:
        async for questions in structure:
            _logger.info(f"Struct: {type(questions)} - {questions}")

    _logger.info(f"Final Result: {questions}")
    return questions



if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    _logger.setLevel(logging.DEBUG)
    client = AsyncOpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    MODEL_NAME = "gpt-oss:20b"
    QUERY = "Create a practice test question for an easy exam on some Maching learning libraries"
    _logger.info(f"Connecting to Ollama using Model: {MODEL_NAME}")
    _logger.info(f"Using Query: {QUERY}")

    few_shot_example = create_few_shot_json()
    json_schema_prompt = create_json_schema_prompt()
    messages = [
        {"role": "system", "content": f"You are a helpful assistant that returns only a json object based on the following schema instruction and example. SCHEMA: {json_schema_prompt} EXAMPLE: {to_json(few_shot_example)}"},
            {"role": "user", "content": QUERY}
        ]

    asyncio.run(main(client, messages))


