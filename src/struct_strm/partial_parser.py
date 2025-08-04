import tree_sitter_json as ts_json
from tree_sitter import Language, Parser, Query, QueryCursor
from struct_strm.tree_queries import get_queries, get_str_keys
from struct_strm.llm_response_handler import openai_chunk_handler, ContinueSignal
from typing import AsyncGenerator, Any, Union
import logging

_logger = logging.getLogger(__name__)


# ----- update for "generic" case -----------
# What's covered:
# - objects with up to one nested structure
# - Always return object or dict
# What’s not covered
# - more complex structures (dicts)
# - Assume all responses are strings (not going to convert to other types)
# - Higher levels of nesting


async def parse_query_matches(matches: list[tuple[int, dict]], snapshot: bytes):
    # query must look for key + values
    results = {}
    for idx, capture_dict in matches:
        key_nodes = capture_dict.get("key")
        value_nodes = capture_dict.get("value")
        _logger.debug(f"Got Key: {key_nodes}")
        _logger.debug(f"Got Values: {value_nodes}")
        if key_nodes is None or value_nodes is None:
            continue
        key_node = key_nodes[0]
        value_node = value_nodes[0]

        pair_key = (
            snapshot[key_node.start_byte : key_node.end_byte].decode("utf8").strip('"')
        )
        pair_value = (
            snapshot[value_node.start_byte : value_node.end_byte]
            .decode("utf8")
            .strip('"')
        )
        # maybe same logic, just append for list?
        # need to assocaite the l2 struct with its related key and structure (so we know how to append)
        results.update({pair_key: pair_value})
    return results


async def parse_query_matches_list(
    matches: list[tuple[int, dict]], snapshot: bytes, nested_cls: type
):
    # In this case the whole list dict must be returned (but not the whole list)
    # aslo need to propigate / match query that uses "object" matching with this one
    results = []
    result_idx = -1
    dict_pair_end_byte = 0
    current_dict_end_byte = 0
    # the problem is we are going to get a flat list here, but we need to parition it by struct
    for idx, capture_dict in matches:
        # handle none case later
        dict_pair_end_byte = capture_dict.get("obj")[0].end_byte
        if dict_pair_end_byte != current_dict_end_byte:
            current_dict_end_byte = dict_pair_end_byte
            result_idx += 1
            results.insert(result_idx, {})

        key_nodes = capture_dict.get("key")
        value_nodes = capture_dict.get("value")
        _logger.debug(f"Got Key: {key_nodes}")
        _logger.debug(f"Got Values: {value_nodes}")
        if key_nodes is None or value_nodes is None:
            continue

        key_node = key_nodes[0]
        value_node = value_nodes[0]
        pair_key = (
            snapshot[key_node.start_byte : key_node.end_byte].decode("utf8").strip('"')
        )
        pair_value = (
            snapshot[value_node.start_byte : value_node.end_byte]
            .decode("utf8")
            .strip('"')
        )
        _logger.debug(f"Pair Results: {results}")
        # maybe same logic, just append for list?
        # need to assocaite the l2 struct with its related key and structure (so we know how to append)
        results[result_idx].update({pair_key: pair_value})
    return results


async def parse_query_matches_list_partial(
    matches: list[tuple[int, dict]], snapshot: bytes, nested_cls: type
):
    # In this case we'll attempt to construct elements in the list
    # before they are completed. The issue is that we don't have a gauruntee of ordering

    results = []
    result_idx = -1
    num_elements = await get_str_keys(nested_cls)
    num_elements = len(num_elements)
    group_num = 0
    # the problem is we are going to get a flat list here, should be in order by bytes?
    for idx, element_match in enumerate(matches):
        _, capture_dict = element_match
        # handle none case later
        if idx == num_elements * (result_idx + 1):
            result_idx += 1
            results.insert(result_idx, {})

        key_nodes = capture_dict.get("key")
        value_nodes = capture_dict.get("value")
        _logger.debug(f"Got Key: {key_nodes}")
        _logger.debug(f"Got Values: {value_nodes}")
        if key_nodes is None or value_nodes is None:
            continue

        key_node = key_nodes[0]
        value_node = value_nodes[0]
        pair_key = (
            snapshot[key_node.start_byte : key_node.end_byte].decode("utf8").strip('"')
        )
        pair_value = (
            snapshot[value_node.start_byte : value_node.end_byte]
            .decode("utf8")
            .strip('"')
        )
        _logger.debug(f"Pair Results: {results}")
        # maybe same logic, just append for list?
        # need to assocaite the l2 struct with its related key and structure (so we know how to append)
        results[result_idx].update({pair_key: pair_value})
    return results


async def query_tree_l1(
    snapshot: bytes, query_str: str, parser: Parser, lang: Language
) -> dict:
    tree = parser.parse(snapshot)
    query = Query(lang, query_str)
    matches = QueryCursor(query).matches(tree.root_node)
    results = await parse_query_matches(matches, snapshot)

    return results


# how to handle lists better?
async def query_tree_l2(
    snapshot: bytes, queries: dict[str, dict[str, any]], parser: Parser, lang: Language
) -> dict[str, list[str]]:
    # we need {"l1_key_01": [{stuff:..., more_stuff: ....}, ...], "l1_key_02": [{stuff:..., more_stuff:...}, ...]}
    # this query is specifically for values that are arrays
    tree = parser.parse(snapshot)
    result_set = {}
    key = None
    for key, query_key in queries.items():
        # query ex - {"key_01": "...", "key_02": "str..."}
        query = Query(lang, query_key["query_str"])
        matches = QueryCursor(query).matches(tree.root_node)
        # were getting all key value pairs as lists, but instead we need to update
        results = await parse_query_matches_list_partial(
            matches, snapshot, query_key["nested_type"]
        )

        result_set.update({key: results})

    if key is None:
        return {}

    return result_set



async def tree_sitter_parse(
    struct: type[Any], 
    response_stream: AsyncGenerator[str, None],
    source:str = None
) -> AsyncGenerator[Union[type[Any], dict], None]:
    # return an instance of the struct for every response
    response = struct()
    buffer = ""
    JSON_LANG = Language(ts_json.language())
    parser = Parser(JSON_LANG)

    queries: tuple[str, dict[str, dict[str, any]]] = await get_queries(struct)

    l1_query = queries[0]
    l2_queries = queries[1]
    part_l1 = {}
    part_l2 = {}

    async for chunk in response_stream:
        if source == "openai":
            try:
                chunk = await openai_chunk_handler(chunk)
            except ContinueSignal:
                continue
            except Exception as e:
                _logger.error(f"Error in openai_chunk_handler: {e}")
                continue

        buffer = buffer + chunk
        buffer_closed = buffer + '"'
        if l1_query is not None:
            part_l1 = await query_tree_l1(
                buffer_closed.encode("utf8"), l1_query, parser, JSON_LANG
            )
        if l2_queries is not None:
            part_l2 = await query_tree_l2(
                buffer_closed.encode("utf8"), l2_queries, parser, JSON_LANG
            )
        part_l1.update(part_l2)
        _logger.debug(f"Creating {struct} with data: {part_l1}")
        _logger.debug(f"For stream {buffer}")
        response = struct(**part_l1)
        yield response