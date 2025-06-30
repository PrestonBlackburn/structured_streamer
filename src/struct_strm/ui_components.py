from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Generator, List
from struct_strm.default_structs import (
    DefaultListStruct, 
    DefaultListItem, 
    get_struct_keys
)
from struct_strm.env import template 
from struct_strm.partial_parser import parse_list_json


@dataclass
class AbstractComponent(ABC):
    """
    Components may have 3 stages - 
    1. pre llm response placeholder rendering
    2. partial rendering with the llm stream
    3. the complete render which may enrich the component
    """

    @abstractmethod
    async def placeholder_render(
            self, 
            **kwargs) -> Generator[str, None, None]:
        pass

    @abstractmethod
    async def partial_render(
            self, 
            response_stream: Generator[str, None, None],
            **kwargs) -> Generator[str, None, None]:
        pass

    @abstractmethod
    async def complete_render(
            self, 
            **kwargs) -> Generator[str, None, None]:
        pass

    @abstractmethod
    async def render(self, **kwargs) -> Generator[str, None, None]:
        pass


@dataclass
class ListComponent(AbstractComponent):
    # mostly just a simple example for testing
    items: List[str] = field(default_factory=list)
    # default_struct: ListStruct = field(default_factory=ListStruct)

    async def placeholder_render(
            self, 
            **kwargs) -> Generator[str, None, None]:
        # fetch placeholer template
        placeholder_template = template("list/list_placeholder.html")
        component = placeholder_template.render()
        yield component

    async def partial_render(
            self, 
            response_stream: Generator[str, None, None], 
            ListType = DefaultListStruct,
            ItemType = DefaultListItem,
            **kwargs) -> Generator[str, None, None]:
        # parse the string stream into objects that make sense
        partial_template = template("list/list_partial.html")
        # example format (as json string):
        # """{"items": [{"item": "apple orange"}, {"item": "banana kiwi grape"}, {"item": "mango pineapple"}]}"""
        # basically just pull out "item" from the items list as they come
        start_key = get_struct_keys(ListType)[0] # should only have one key
        item_key = get_struct_keys(ItemType)[0] # should only have one item key
        items_list: Generator = parse_list_json(response_stream, start_key=start_key, item_key=item_key)
        async for streamed_items in items_list:
            self.items = streamed_items
            yield partial_template.render(item=[streamed_items])

    async def complete_render(
            self, 
            **kwargs) -> Generator[str, None, None]:
        # render complete component with processssing
        complete_template = template("list/list_complete.html")
        yield complete_template.render(items=self.items)

    async def render(
            self, 
            response_stream: Generator[str, None, None], 
            **kwargs) -> Generator[str, None, None]:
        # render the component in 3 stages

        async for item in self.placeholder_render(**kwargs):
            yield item
        async for item in self.partial_render(response_stream, **kwargs):
            yield item
        async for item in self.complete_render(**kwargs):
            yield item

