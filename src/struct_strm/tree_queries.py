from typing import Any, get_origin, get_args
from dataclasses import is_dataclass
from pydantic import BaseModel

import logging

_logger = logging.getLogger(__name__)
# right now just going to focus on single and "two level" structs
# note - nested structures must have different keys than parents

async def get_str_keys(StreamedStruct: type[Any]) -> list[str]:
    # right now only supporting string fields (no arrays, numbers will be "strings")
    # also won't handle optional strings,
    # but really there should always be a default that is not noe
    l1_fields = []

    if issubclass(StreamedStruct, BaseModel):
        _logger.debug(f"Got Pydantic Class: {StreamedStruct}")
        fields = StreamedStruct.model_fields.items()
        for name, field_type in fields:
            if field_type.annotation == str:
                l1_fields.append(name)
    elif is_dataclass(StreamedStruct):
        _logger.debug(f"Got Dataclass Class {StreamedStruct}")
        fields = StreamedStruct.__annotations__.items()
        for name, field_type in fields:
            if field_type == str:
                l1_fields.append(name)
    else:
        raise ValueError(f"Expected Pydantic model or dataclass, got: {StreamedStruct}")

    return l1_fields


async def has_structure(annotation: Any) -> bool:
    origin = get_origin(annotation)
    args = get_args(annotation)
    # Check for array of "SomeClass"
    if origin in (list, tuple, set):
        inner = args[0] if args else None
        if isinstance(inner, type) and (
            issubclass(inner, BaseModel) or is_dataclass(inner)
        ):
            return True
    # If structure
    if isinstance(annotation, type) and (
        issubclass(annotation, BaseModel) or is_dataclass(annotation)
    ):
        return True

    return False


async def has_nested_structure(StreamedStruct: type[Any]) -> bool:
    # check l2 (nested) structs for both dataclass and basemodel
    if issubclass(StreamedStruct, BaseModel):
        _logger.debug(f"Got Pydantic Class: {StreamedStruct}")
        annotations = [
            field_type.annotation
            for name, field_type in StreamedStruct.model_fields.items()
        ]
    elif is_dataclass(StreamedStruct):
        _logger.debug(f"Got Dataclass Class {StreamedStruct}")
        annotations = StreamedStruct.__annotations__.values()
    else:
        raise ValueError(f"Expected Pydantic model or dataclass, got: {StreamedStruct}")

    annotations_with_nested_struct = [
        await has_structure(annotation) for annotation in annotations
    ]
    has_l2 = any(annotations_with_nested_struct)
    return has_l2


async def get_struct_fields(StreamedStruct: type[Any]) -> dict:
    # technically dict_items list of tuple with key/value

    if issubclass(StreamedStruct, BaseModel):
        fields = StreamedStruct.model_fields.items()
    elif is_dataclass(StreamedStruct):
        fields = StreamedStruct.__annotations__.items()
    else:
        raise ValueError(f"Expected Pydantic model or dataclass, got: {StreamedStruct}")
    _logger.debug(f"Fields For Array {fields}")
    return fields


async def get_array_keys(
    StreamedStruct: type[Any],
) -> list[tuple[list[str], str, type]]:
    array_keys: list[tuple[list[str], str, type]] = []

    fields = await get_struct_fields(StreamedStruct)
    _logger.debug(f"Fields For Array {fields}")
    for key, field_info in fields:
        if issubclass(StreamedStruct, BaseModel):
            annotation = field_info.annotation
        else:
            annotation = field_info
        origin = get_origin(annotation)
        args = get_args(annotation)
        _logger.debug(f"Array Origin {origin}")
        _logger.debug(f"Array Args {args}")
        if origin in (list, tuple, set):
            inner_cls = args[0] if args else None
            # get the key for the inner class (prob need to iterate for multiple keys)
            if inner_cls is None:
                raise ValueError("nested classes must be structs")
            inner_keys: list[str] = await get_str_keys(inner_cls)
            if isinstance(inner_cls, type) and (
                issubclass(inner_cls, BaseModel) or is_dataclass(inner_cls)
            ):
                array_keys.append((inner_keys, key, inner_cls))

    return array_keys


async def get_query_l1(StreamedStruct: type[Any]) -> str:

    top_keys = await get_str_keys(StreamedStruct)
    top_keys_formatted = [f'"\\"{key}\\""' for key in top_keys]
    top_keys_str = "\n".join(top_keys_formatted)
    query_str = f"""(
        (pair
            key: (string) @key
            value: (string) @value)
        (#any-of? @key
            {top_keys_str}
        )
    """
    return query_str


async def get_query_l2(
    StreamedStruct: type[Any], group_by_object: bool = False
) -> dict[str, dict[str, str]]:
    # really this only works if there is only one child array
    # will revisit in the future, but I think that's all I need
    # return in format - {"struct_key_01": query_01, "struct_key_02": query_02}
    queries = {}
    top_keys = await get_str_keys(StreamedStruct)
    filter_keys_str = ""

    if top_keys != []:
        filter_keys_formatted = [f'(#not-eq? @key "\\"{key}\\"")' for key in top_keys]
        filter_keys_str = "\n".join(filter_keys_formatted)

    array_keys: list[tuple[list[str], str, type]] = await get_array_keys(StreamedStruct)
    _logger.debug(f"Array Keys: {array_keys}")
    # need to get the nested key back if we want to recurse later
    for inner_keys, top_key, nested_type in array_keys:
        inner_keys_formatted = [f'"\\"{key}\\""' for key in inner_keys]
        inner_keys_str = "\n".join(inner_keys_formatted)
        if group_by_object:
            query_str = f"""(
            (object
                (pair
                    key: (string) @key
                    value: (string) @value)
                {filter_keys_str}
                (#any-of? @key {inner_keys_str})
            )) @obj
            """
        else:
            query_str = f"""(
                (pair
                    key: (string) @key
                    value: (string) @value)
                {filter_keys_str}
                (#any-of? @key {inner_keys_str})
            )
            """

        queries.update({top_key: {"query_str": query_str, "nested_type": nested_type}})
    _logger.debug(f"got l2 queries: {queries}")

    return queries


async def get_queries(
    StreamedStruct: type[Any],
    group_by_object: bool = False,
) -> tuple[str | None, dict[str, dict[str, str]] | None]:
    # tuple of l1 and l2 queries
    # check l1 and l2 keys

    # if has no l1 keys then we can skip
    has_l1_key = await get_str_keys(StreamedStruct) != []
    # need to check for nested structures
    has_l2_key = await has_nested_structure(StreamedStruct)

    l1_query = None
    l2_query = None

    if has_l1_key:
        _logger.debug("Has L1 Keys")
        l1_query = await get_query_l1(StreamedStruct)

    if has_l2_key:
        _logger.debug("Has L2 Keys")
        l2_query = await get_query_l2(StreamedStruct, group_by_object=group_by_object)

    return (l1_query, l2_query)
