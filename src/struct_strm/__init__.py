__all__ = [
    "tree_sitter_parse",

    "aget_openai_client",
    "openai_stream_wrapper",
    "parse_openai_stream",
    "parse_hf_stream",
    
    "to_json",
    "to_dict",
]

from struct_strm.partial_parser import (
    tree_sitter_parse,
)



from struct_strm.llm_clients import aget_openai_client
from struct_strm.llm_wrappers import (
    openai_stream_wrapper, 
    parse_openai_stream,
    parse_hf_stream,
)
from struct_strm.compat import to_dict, to_json


# ---- Optional -----
import logging

_logger = logging.getLogger(__name__)

try:
    from pydantic import BaseModel
    HAS_PYDANTIC = True
except Exception as e:
    _logger.warning(f"Warning: Pydantic Not Installed, some example features may be univailable.")
    HAS_PYDANTIC = False

try: 
    from jinja2 import Environment
    HAS_JINJA = True
except Exception as e:
    _logger.warning(f"Warning: Jinja2 Not Installed, some example features may be univailable.")
    HAS_JINJA = False

if HAS_JINJA and HAS_PYDANTIC:
    # ---- Optional Features ----
    __all__.extend([
    "ListComponent",
    "FormComponent",
    "TableComponent",
    "RubricComponent",
    
    # mock examples -
    "simulate_stream_list_struct",
    "simulate_stream_openai",
    "simulate_stream_form_struct",
    "simulate_stream_form_openai",
    ])

    from struct_strm.ui_components import (
        ListComponent, 
        FormComponent,
        TableComponent,
        RubricComponent,
    )

    from struct_strm.structs.list_structs import (
        simulate_stream_list_struct,
        simulate_stream_openai,
    )
    from struct_strm.structs.form_structs import (
        simulate_stream_form_struct,
        simulate_stream_form_openai,
    )


from ._version import version as __version__

