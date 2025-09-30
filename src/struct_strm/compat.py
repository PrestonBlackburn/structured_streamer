from typing import Any
import json
from dataclasses import is_dataclass, asdict

try:
    from pydantic import BaseModel

    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    BaseModel = None


def is_pydantic_model(cls: Any) -> bool:
    is_pydantic_model = False
    if BaseModel is not None:
        if issubclass(cls, BaseModel):
            is_pydantic_model = True
    return is_pydantic_model


def to_json(obj: Any) -> str:
    # class instance of pydantic model or dataclass to json
    if HAS_PYDANTIC and is_pydantic_model(obj):
        return obj.model_dump_json()
    elif is_dataclass(obj) and not isinstance(obj, type):
        return json.dumps(asdict(obj))
    else:
        raise TypeError(f"Unsupported Type: {type(obj)}")


def to_dict(obj: Any) -> dict[str, Any]:
    if HAS_PYDANTIC and is_pydantic_model(obj):
        return obj.model_dump()
    elif is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    else:
        raise TypeError(f"Unsupported Type: {type(obj)}")
