from typing import AsyncGenerator, List, Dict, Tuple, Optional, Type, Union
import enum
from copy import deepcopy
from abc import ABC, abstractmethod
import logging

_logger = logging.getLogger(__name__)


async def parse_list_json(
    response_stream: AsyncGenerator[str, None],
    start_key: str = "items",
    item_key: str = "item",
) -> AsyncGenerator[List[str], None]:

    buffer = ""
    inside_items = False
    inside_item = False
    current_item_value = ""
    item_idx = -1
    item_values: Dict[int, str] = {}

    async for chunk in response_stream:
        # chunk = chunk.strip()

        if not chunk:
            continue

        buffer += chunk

        if not inside_items and f'"{start_key}":' in buffer:
            inside_items = True
            buffer = buffer.split(start_key, 1)[1]
            continue

        if inside_items:
            if not inside_item:
                if f'"{item_key}":' in buffer:
                    inside_item = True
                    current_item_value = ""
                    item_idx += 1  # new item started
                    after_key = buffer.split(item_key, 1)[1]
                    if ":" in after_key:
                        buffer = after_key.split(":", 1)[1]
                    else:
                        buffer = ""
                    continue

            if inside_item:
                if chunk in {"}", "]", "},", '},{"'}:
                    inside_item = False
                    continue

                # Stream token into current item value
                # if chunk not in {":", '"', "'", ","}:
                if chunk not in {'"', "'", ","}:
                    current_item_value += chunk
                    clean = current_item_value.strip().strip('"').strip(",")
                    if item_values.get(item_idx) != clean:
                        item_values[item_idx] = clean
                        yield [item_values[i] for i in sorted(item_values.keys())]


# ------ Messing Around with a State Machine ----------
# For some reason I thought this would make it easier?


class FormState(ABC):
    @abstractmethod
    async def execute(
        self, buffer: str, current_chunk: str
    ) -> AsyncGenerator[str, None]: ...

    @abstractmethod
    async def next_state(self) -> AsyncGenerator[Union[Type, "FormState"], None]: ...


class FormDescState(FormState):
    def __init__(
        self,
        results: dict,
        field_description_key: str = "field_placeholder",
        field_idx: int = -1,
    ):
        self.results = results
        self.in_state = False
        # self.in_pair = True
        self.field_description_key = field_description_key
        self.field_idx = field_idx
        self.desc = ""

    async def execute(
        self, buffer: str, current_chunk: str
    ) -> AsyncGenerator[str, None]:
        _logger.debug("execute FormDescState")
        item_termintors = {
            '"',
            "'",
            ",",
        }  # TODO - see if we can prompt for better terminators
        pair_terminators = {"}", "]", "},", '},{"', "}]"}  # go back to name

        if not self.in_state and f'"{self.field_description_key}":' in buffer:
            self.in_state = True

            key_idx = buffer.find(f'"{self.field_description_key}":')
            if key_idx != -1:
                buffer = buffer[key_idx + len(f'"{self.field_description_key}":') :]
            else:
                buffer = ""

        if self.in_state:
            # check for terminators + append current values
            if any(value in current_chunk for value in pair_terminators):
                # if it is a terminator don't add it to the result set
                self.in_state = False
                self.desc = ""
                buffer = current_chunk

            elif current_chunk not in item_termintors:
                _logger.debug(f"Desc chunk: {current_chunk}")
                self.desc += current_chunk
                self.desc = self.desc.strip('"').strip(",")
                self.results[self.field_idx][self.field_description_key] = self.desc
            else:
                # reset
                self.in_state = False
                self.desc = ""

            return buffer

        # if self.in_pair and current_chunk in pair_terminators:
        #     self.in_pair = False

        return buffer

    async def next_state(self) -> AsyncGenerator[Union[Type, Dict], None]:
        # in/out
        if self.in_state:
            return self
        if not self.in_state:  # and not self.in_pair:
            return FormNameState(
                results=self.results,
                field_description_key=self.field_description_key,
                field_idx=self.field_idx,
            )


class FormNameState(FormState):
    def __init__(
        self,
        results: dict,
        field_name_key: str = "field_name",
        field_description_key: str = "field_placeholder",
        field_idx: int = -1,
    ):
        self.results = results
        self.in_state = False
        self.field_name_key = field_name_key
        self.field_description_key = field_description_key
        self.field_idx = field_idx
        self.name = ""

    async def execute(
        self, buffer: str, current_chunk: str
    ) -> AsyncGenerator[str, None]:
        _logger.debug("execute FormNameState")
        item_termintors = {
            '"',
            "'",
            ",",
            f"{self.field_description_key}",
        }  # TODO - see if we can prompt for better terminators
        pair_terminators = {
            "}",
            "]",
            "},",
            '},{"',
            "}]",
            f'"{self.field_description_key}"',
        }

        if not self.in_state and f'"{self.field_name_key}":' in buffer:
            _logger.debug(f"IN FIELD NAME: {buffer}")
            self.in_state = True
            # init new row
            self.field_idx += 1
            self.results.update(
                {
                    self.field_idx: {
                        self.field_name_key: "",
                        self.field_description_key: "",
                    }
                }
            )
            _logger.debug(f"Added Results: {self.results}")
            key_idx = buffer.find(f'"{self.field_description_key}":')
            if key_idx != -1:
                buffer = buffer[key_idx + len(f'"{self.field_description_key}":') :]
            else:
                buffer = ""

        if self.in_state:
            if any(term in current_chunk for term in pair_terminators):
                _logger.debug(f"Name done: {self.name}")
                self.in_state = False
                self.name = ""
            # check for terminators + append current values
            elif current_chunk not in item_termintors:
                _logger.debug(f"NAME CHUNK: {current_chunk}")
                self.name += current_chunk
                self.name = self.name.strip().strip('"').strip(",")
                self.results[self.field_idx][self.field_name_key] = self.name
            else:
                # reset
                self.in_state = False
                self.name = ""
        return buffer

    async def next_state(self) -> AsyncGenerator[Type, None]:
        # in/out
        if self.in_state:
            return self
        else:
            return FormDescState(
                results=self.results,
                field_description_key=self.field_description_key,
                field_idx=self.field_idx,
            )


class FormInitState(FormState):
    # entry
    def __init__(
        self,
        results: dict,
        start_key: str = "form_fields",
        field_name_key: str = "field_name",
        field_description_key: str = "field_placeholder",
        field_idx: int = -1,
    ):
        self.results = results
        self.in_state = False
        self.start_key = start_key
        self.field_name_key = field_name_key
        self.field_description_key = field_description_key
        self.field_idx = field_idx

    async def execute(
        self, buffer: str, current_chunk: str
    ) -> AsyncGenerator[str, None]:
        _logger.debug("execute FormInitState")
        if not self.in_state and f'"{self.start_key}":' in buffer:
            self.in_state = True
            # start getting the content
            buffer = buffer.split(self.start_key, 1)[1]
            return buffer
        return buffer

    async def next_state(self) -> AsyncGenerator[Type, None]:
        # in/out
        if self.in_state == True:
            return FormNameState(
                self.results,
                field_name_key=self.field_name_key,
                field_description_key=self.field_description_key,
                field_idx=self.field_idx,
            )
        if self.in_state == False:
            pass


async def parse_form_json_fsm(
    response_stream: AsyncGenerator[str, None],
    start_key: str = "form_fields",
    field_name_key: str = "field_name",
    field_description_key: str = "field_placeholder",
) -> AsyncGenerator[dict, None]:
    results = {}
    buffer = ""
    state = FormInitState(
        results,
        start_key=start_key,
        field_name_key=field_name_key,
        field_description_key=field_description_key,
    )
    async for chunk in response_stream:
        buffer = buffer + chunk
        buffer = await state.execute(buffer, chunk)
        next_state = await state.next_state()
        if next_state and next_state != state:
            state = next_state
        yield deepcopy(state.results)
