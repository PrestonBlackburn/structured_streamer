import pytest
from struct_strm.llm_wrappers import openai_stream_wrapper
from struct_strm.llm_clients import aget_openai_client
from struct_strm.structs.list_structs import DefaultListItem, DefaultListStruct

prompt_context = ""
user_query = "Create list describing 5 open source llm tools"


# @pytest.mark.asyncio
async def openai_response():
    stream = openai_stream_wrapper(
        user_query,
        prompt_context,
        DefaultListStruct,
    )

    return True
