import tree_sitter_json as ts_json
from tree_sitter import Language, Parser, Query, QueryCursor, Node
from struct_strm.tree_queries import get_queries, get_str_keys
from typing import AsyncGenerator, List, Dict, Any, Tuple, Optional, Type, Union
import enum
from copy import deepcopy
from abc import ABC, abstractmethod
import logging
from pydantic import BaseModel

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
    struct: type[Any], response_stream: AsyncGenerator[str, None]
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



def get_struct_keys(struct: BaseModel) -> List[str]:
    return list(struct.model_fields.keys())


# async def parse_list_json(
#     response_stream: AsyncGenerator[str, None],
#     start_key: str = "items",
#     item_key: str = "item",
# ) -> AsyncGenerator[List[str], None]:

#     buffer = ""
#     inside_items = False
#     inside_item = False
#     current_item_value = ""
#     item_idx = -1
#     item_values: Dict[int, str] = {}

#     async for chunk in response_stream:
#         # chunk = chunk.strip()

#         if not chunk:
#             continue

#         buffer += chunk

#         if not inside_items and f'"{start_key}":' in buffer:
#             inside_items = True
#             buffer = buffer.split(start_key, 1)[1]
#             continue

#         if inside_items:
#             if not inside_item:
#                 if f'"{item_key}":' in buffer:
#                     inside_item = True
#                     current_item_value = ""
#                     item_idx += 1  # new item started
#                     after_key = buffer.split(item_key, 1)[1]
#                     if ":" in after_key:
#                         buffer = after_key.split(":", 1)[1]
#                     else:
#                         buffer = ""
#                     continue

#             if inside_item:
#                 if chunk in {"}", "]", "},", '},{"'}:
#                     inside_item = False
#                     continue

#                 # Stream token into current item value
#                 # if chunk not in {":", '"', "'", ","}:
#                 if chunk not in {'"', "'", ","}:
#                     current_item_value += chunk
#                     clean = current_item_value.strip().strip('"').strip(",")
#                     if item_values.get(item_idx) != clean:
#                         item_values[item_idx] = clean
#                         yield [item_values[i] for i in sorted(item_values.keys())]


# # ------ Messing Around with a State Machine ----------
# # For some reason I thought this would make it easier?


# class FormState(ABC):
#     @abstractmethod
#     async def execute(
#         self, buffer: str, current_chunk: str
#     ) -> AsyncGenerator[str, None]: ...

#     @abstractmethod
#     async def next_state(self) -> AsyncGenerator[Union[Type, "FormState"], None]: ...


# class FormDescState(FormState):
#     def __init__(
#         self,
#         results: dict,
#         field_description_key: str = "field_placeholder",
#         field_idx: int = -1,
#     ):
#         self.results = results
#         self.in_state = False
#         # self.in_pair = True
#         self.field_description_key = field_description_key
#         self.field_idx = field_idx
#         self.desc = ""

#     async def execute(
#         self, buffer: str, current_chunk: str
#     ) -> AsyncGenerator[str, None]:
#         _logger.debug("execute FormDescState")
#         item_termintors = {
#             '"',
#             "'",
#             ",",
#         }  # TODO - see if we can prompt for better terminators
#         pair_terminators = {"}", "]", "},", '},{"', "}]"}  # go back to name

#         if not self.in_state and f'"{self.field_description_key}":' in buffer:
#             self.in_state = True

#             key_idx = buffer.find(f'"{self.field_description_key}":')
#             if key_idx != -1:
#                 buffer = buffer[key_idx + len(f'"{self.field_description_key}":') :]
#             else:
#                 buffer = ""

#         if self.in_state:
#             # check for terminators + append current values
#             if any(value in current_chunk for value in pair_terminators):
#                 # if it is a terminator don't add it to the result set
#                 self.in_state = False
#                 self.desc = ""
#                 buffer = current_chunk

#             elif current_chunk not in item_termintors:
#                 _logger.debug(f"Desc chunk: {current_chunk}")
#                 self.desc += current_chunk
#                 self.desc = self.desc.strip('"').strip(",")
#                 self.results[self.field_idx][self.field_description_key] = self.desc
#             else:
#                 # reset
#                 self.in_state = False
#                 self.desc = ""

#             return buffer

#         # if self.in_pair and current_chunk in pair_terminators:
#         #     self.in_pair = False

#         return buffer

#     async def next_state(self) -> AsyncGenerator[Union[Type, Dict], None]:
#         # in/out
#         if self.in_state:
#             return self
#         if not self.in_state:  # and not self.in_pair:
#             return FormNameState(
#                 results=self.results,
#                 field_description_key=self.field_description_key,
#                 field_idx=self.field_idx,
#             )


# class FormNameState(FormState):
#     def __init__(
#         self,
#         results: dict,
#         field_name_key: str = "field_name",
#         field_description_key: str = "field_placeholder",
#         field_idx: int = -1,
#     ):
#         self.results = results
#         self.in_state = False
#         self.field_name_key = field_name_key
#         self.field_description_key = field_description_key
#         self.field_idx = field_idx
#         self.name = ""

#     async def execute(
#         self, buffer: str, current_chunk: str
#     ) -> AsyncGenerator[str, None]:
#         _logger.debug("execute FormNameState")
#         item_termintors = {
#             '"',
#             "'",
#             ",",
#             f"{self.field_description_key}",
#         }  # TODO - see if we can prompt for better terminators
#         pair_terminators = {
#             "}",
#             "]",
#             "},",
#             '},{"',
#             "}]",
#             f'"{self.field_description_key}"',
#         }

#         if not self.in_state and f'"{self.field_name_key}":' in buffer:
#             _logger.debug(f"IN FIELD NAME: {buffer}")
#             self.in_state = True
#             # init new row
#             self.field_idx += 1
#             self.results.update(
#                 {
#                     self.field_idx: {
#                         self.field_name_key: "",
#                         self.field_description_key: "",
#                     }
#                 }
#             )
#             _logger.debug(f"Added Results: {self.results}")
#             key_idx = buffer.find(f'"{self.field_description_key}":')
#             if key_idx != -1:
#                 buffer = buffer[key_idx + len(f'"{self.field_description_key}":') :]
#             else:
#                 buffer = ""

#         if self.in_state:
#             if any(term in current_chunk for term in pair_terminators):
#                 _logger.debug(f"Name done: {self.name}")
#                 self.in_state = False
#                 self.name = ""
#             # check for terminators + append current values
#             elif current_chunk not in item_termintors:
#                 _logger.debug(f"NAME CHUNK: {current_chunk}")
#                 self.name += current_chunk
#                 self.name = self.name.strip().strip('"').strip(",")
#                 self.results[self.field_idx][self.field_name_key] = self.name
#             else:
#                 # reset
#                 self.in_state = False
#                 self.name = ""
#         return buffer

#     async def next_state(self) -> AsyncGenerator[Type, None]:
#         # in/out
#         if self.in_state:
#             return self
#         else:
#             return FormDescState(
#                 results=self.results,
#                 field_description_key=self.field_description_key,
#                 field_idx=self.field_idx,
#             )


# class FormInitState(FormState):
#     # entry
#     def __init__(
#         self,
#         results: dict,
#         start_key: str = "form_fields",
#         field_name_key: str = "field_name",
#         field_description_key: str = "field_placeholder",
#         field_idx: int = -1,
#     ):
#         self.results = results
#         self.in_state = False
#         self.start_key = start_key
#         self.field_name_key = field_name_key
#         self.field_description_key = field_description_key
#         self.field_idx = field_idx

#     async def execute(
#         self, buffer: str, current_chunk: str
#     ) -> AsyncGenerator[str, None]:
#         _logger.debug("execute FormInitState")
#         if not self.in_state and f'"{self.start_key}":' in buffer:
#             self.in_state = True
#             # start getting the content
#             buffer = buffer.split(self.start_key, 1)[1]
#             return buffer
#         return buffer

#     async def next_state(self) -> AsyncGenerator[Type, None]:
#         # in/out
#         if self.in_state == True:
#             return FormNameState(
#                 self.results,
#                 field_name_key=self.field_name_key,
#                 field_description_key=self.field_description_key,
#                 field_idx=self.field_idx,
#             )
#         if self.in_state == False:
#             pass


# async def parse_form_json_fsm(
#     response_stream: AsyncGenerator[str, None],
#     start_key: str = "form_fields",
#     field_name_key: str = "field_name",
#     field_description_key: str = "field_placeholder",
# ) -> AsyncGenerator[dict, None]:
#     results = {}
#     buffer = ""
#     state = FormInitState(
#         results,
#         start_key=start_key,
#         field_name_key=field_name_key,
#         field_description_key=field_description_key,
#     )
#     async for chunk in response_stream:
#         buffer = buffer + chunk
#         buffer = await state.execute(buffer, chunk)
#         next_state = await state.next_state()
#         if next_state and next_state != state:
#             state = next_state
#         yield deepcopy(state.results)


# # ------------------------------------------------------------
# # -------------------  Is this a tree sitter -----------------
# # ------------------------------------------------------------


# async def query_form_json_struct(
#     snapshot: bytes,
#     field_name_key: str,
#     field_description_key: str,
#     parser: Parser,
#     lang: Language,
# ) -> dict[int, dict[str, str]]:
#     # I feel like there is some way to generalize this...
#     query_string = """
#     (pair
#         key: (string) @key
#         value: (string) @value) @pair
#     """

#     result_placeholder = {field_name_key: "", field_description_key: ""}
#     query_results = {}
#     tree = parser.parse(snapshot)
#     query = Query(lang, query_string)
#     # captures = QueryCursor(query).captures(tree.root_node)
#     matches = QueryCursor(query).matches(tree.root_node)
#     pair_count = -1
#     for idx, capture_dict in matches:
#         key_nodes = capture_dict.get("key")
#         value_nodes = capture_dict.get("value")
#         if key_nodes is None or value_nodes is None:
#             continue
#         key_node = key_nodes[0]
#         value_node = value_nodes[0]
#         # ex: field_name or field_placeholder
#         pair_key = (
#             snapshot[key_node.start_byte : key_node.end_byte].decode("utf8").strip('"')
#         )
#         # ex: "fruits" or "apple banana..."
#         pair_value = (
#             snapshot[value_node.start_byte : value_node.end_byte]
#             .decode("utf8")
#             .strip('"')
#         )
#         if pair_key == field_name_key:
#             pair_count += 1
#             query_results.update({pair_count: result_placeholder.copy()})
#         if pair_count >= 0 and pair_count in query_results:
#             query_results[pair_count].update({pair_key: pair_value})
#     return query_results


# async def parse_form_json_ts(
#     response_stream: AsyncGenerator[str, None],
#     start_key: str = "form_fields",
#     field_name_key: str = "field_name",
#     field_description_key: str = "field_placeholder",
# ) -> AsyncGenerator[dict, None]:
#     results = {}
#     buffer = ""

#     JSON_LANG = Language(ts_json.language())
#     parser = Parser(JSON_LANG)

#     async for chunk in response_stream:
#         buffer = buffer + chunk
#         buffer_closed = buffer + '"'
#         results = await query_form_json_struct(
#             buffer_closed.encode("utf8"),
#             field_name_key,
#             field_description_key,
#             parser,
#             JSON_LANG,
#         )
#         yield results


# # ----------------- Table Rendering -------------------
# # Example structure (kind of like generic version of last example)
# # [
# #   { "title": "Top Gun", "genre": "Action", "rating": 8.3 },
# #   { "title": "Amélie", "genre": "Romance", "rating": 8.4 }
# # ]
# # class ExampleRow:
# #     title: "Top Gun"
# #     genre: "Action"
# #     rating: "8.3"


# async def query_table_json_struct(
#     snapshot: str, row_struct: BaseModel, parser: Parser, lang: Language
# ) -> list[dict[str, str]]:

#     query_string = """
#     (pair
#         key: (string) @key
#         value: (string) @value) @pair
#     """
#     row_struct_fields = get_struct_keys(row_struct)
#     result_placeholder = {}
#     for field in row_struct_fields:
#         result_placeholder.update({field: ""})

#     query_results = {}
#     tree = parser.parse(snapshot)
#     query = Query(lang, query_string)
#     # captures = QueryCursor(query).captures(tree.root_node)
#     matches = QueryCursor(query).matches(tree.root_node)

#     pair_count = -1
#     for idx, capture_dict in matches:
#         key_nodes = capture_dict.get("key")
#         value_nodes = capture_dict.get("value")
#         if key_nodes is None or value_nodes is None:
#             continue
#         key_node = key_nodes[0]
#         value_node = value_nodes[0]
#         # ex: field_name or field_placeholder
#         pair_key = (
#             snapshot[key_node.start_byte : key_node.end_byte].decode("utf8").strip('"')
#         )
#         # ex: "fruits" or "apple banana..."
#         pair_value = (
#             snapshot[value_node.start_byte : value_node.end_byte]
#             .decode("utf8")
#             .strip('"')
#         )
#         if pair_key == row_struct_fields[0]:
#             pair_count += 1
#             query_results.update({pair_count: result_placeholder.copy()})
#         if pair_count >= 0 and pair_count in query_results:
#             query_results[pair_count].update({pair_key: pair_value})
#     return query_results


# async def parse_table_json_ts(
#     response_stream: AsyncGenerator[str, None], row_struct: BaseModel
# ) -> AsyncGenerator[dict, None]:

#     results = {}
#     buffer = ""

#     JSON_LANG = Language(ts_json.language())
#     parser = Parser(JSON_LANG)

#     async for chunk in response_stream:
#         buffer = buffer + chunk
#         buffer_closed = buffer + '"'
#         results = await query_table_json_struct(
#             buffer_closed.encode("utf8"), row_struct, parser, JSON_LANG
#         )
#         if results == {}:
#             continue
#         yield results
