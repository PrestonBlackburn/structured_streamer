from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Generator, List
from struct_strm.default_structs import ListStruct
from struct_strm.env import template 


@dataclass
class AbstractComponent(ABC):
    """
    Components may have 3 stages - 
    1. pre llm response placeholder rendering
    2. partial rendering with the llm stream
    3. the complete render which may enrich the component
    """
    ...

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
            **kwargs) -> Generator[str, None, None]:
        # parse the string stream into objects that make sense
        partial_template = template("list/list_partial.html")
        # example format (as json string):
        # """{"items": [{"item": "apple orange"}, {"item": "banana kiwi grape"}, {"item": "mango pineapple"}]}"""
        start_key = "items"
        item_key = "item"
        aggregated_items = ""
        streamed_items = []
        # basically just pull out "item" from the items list as they come
        for item in response_stream:
            aggregated_items += item
            # later we can handle quotes
            aggregated_items = aggregated_items.replace('"', '')
            aggregated_items = aggregated_items.replace("'", "")
            if start_key in aggregated_items:
                # then we have a full item
                if item_key in aggregated_items:
                    item_values = aggregated_items.split(f'{item_key}:')[1:]
                    # can revisit this logic later
                    for idx, value in enumerate(item_values):
                        if len(streamed_items) <= idx:
                            if value.endswith("},{"):
                                value = value[:-4]
                            if value.endswith("}]") or value.endswith("},"):
                                value = value[:-4]
                            if value.endswith("}"):
                                value = value[:-3]
                            streamed_items.append(value)
                         
                        # cleanup terminators
                        if value.endswith("},{"):
                            streamed_items[idx] = value[:-3]
                        if value.endswith("},") or value.endswith(",{"):
                            streamed_items[idx] = value[:-3] 
                        if value.endswith("}]"):
                            streamed_items[idx] = value[:-4]
                        if value.endswith("}"):
                            streamed_items[idx] = value[:-3]

            self.items = streamed_items
            yield partial_template.render(item=[streamed_items])
        pass


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

