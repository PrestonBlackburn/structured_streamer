from typing import Union
try:
    from openai.lib.streaming.chat._events import ChunkEvent
except ImportError:
    ChunkEvent = None

from dataclasses import field

# List example with openai
import logging

_logger = logging.getLogger(__name__)


class ContinueSignal(Exception): pass

async def openai_chunk_handler(chunk: ChunkEvent) -> Union[str, ContinueSignal]:
    if ChunkEvent is None:
        raise ImportError("OpenAI library is not available. Please install struct-strm with the openai option - pip install struct-strm[openai].")
    
    if chunk.type == "content.delta":
        chunk = chunk.delta
        _logger.debug(f"Delta: {chunk}")  # get tokens for better mocks
        return chunk
    elif chunk.type == "content.done":
        _logger.debug("OpenAI stream complete")
        raise ContinueSignal()
    elif chunk.type == "error":
        _logger.error(f"Error in stream: {chunk.error}")
        raise ContinueSignal()
    else:
        raise ContinueSignal()

