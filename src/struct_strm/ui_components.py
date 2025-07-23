from abc import ABC, abstractmethod
import asyncio
from dataclasses import dataclass, field
from typing import Generator, List, AsyncGenerator, Dict
from struct_strm.structs.list_structs import (
    DefaultListStruct,
    DefaultListItem,
)
from struct_strm.structs.form_structs import (
    DefaultFormStruct,
    DefaultFormItem,
)
from struct_strm.structs.table_structs import (
    ExampleRow,
    ExampleTableStruct,
)
from struct_strm.template import template
from struct_strm.partial_parser import (
    parse_list_json,
    parse_form_json_fsm,
    parse_form_json_ts,
    get_struct_keys,
    parse_table_json_ts,
)
from pydantic import BaseModel

import logging

_logger = logging.getLogger(__name__)


@dataclass
class AbstractComponent(ABC):
    """
    Components may have 3 stages -
    1. pre llm response placeholder rendering
    2. partial rendering with the llm stream
    3. the complete render which may enrich the component
    """

    @abstractmethod
    async def placeholder_render(self, **kwargs) -> Generator[str, None, None]:
        pass

    @abstractmethod
    async def partial_render(
        self, response_stream: Generator[str, None, None], **kwargs
    ) -> Generator[str, None, None]:
        pass

    @abstractmethod
    async def complete_render(self, **kwargs) -> Generator[str, None, None]:
        pass

    @abstractmethod
    async def render(self, **kwargs) -> Generator[str, None, None]:
        pass


@dataclass
class ListComponent(AbstractComponent):
    # mostly just a simple example for testing
    items: List[str] = field(default_factory=list)
    # default_struct: ListStruct = field(default_factory=ListStruct)
    output: str = field(default="html")  # either output html or incremental json

    async def placeholder_render(self, **kwargs) -> AsyncGenerator[str, None]:
        # fetch placeholer template
        placeholder_template = template("list/list_placeholder.html")
        template_wrapper = template("list/list_container.html")
        component_html = placeholder_template.render()
        yield template_wrapper.render(list_content=component_html)

    async def partial_render(
        self,
        response_stream: AsyncGenerator[str, None],
        ListType=DefaultListStruct,
        ItemType=DefaultListItem,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        # parse the string stream into objects that make sense
        partial_template = template("list/list_partial.html")
        template_wrapper = template("list/list_container.html")
        # example format (as json string):
        # """{"items": [{"item": "apple orange"}, {"item": "banana kiwi grape"}, {"item": "mango pineapple"}]}"""
        # basically just pull out "item" from the items list as they come
        start_key = get_struct_keys(ListType)[0]  # should only have one key
        item_key = get_struct_keys(ItemType)[0]  # should only have one item key
        items_list: AsyncGenerator = parse_list_json(
            response_stream, start_key=start_key, item_key=item_key
        )
        async for streamed_items in items_list:
            self.items = streamed_items
            patial_template_html = partial_template.render(items=list(streamed_items))
            yield template_wrapper.render(list_content=patial_template_html)

    async def complete_render(self, **kwargs) -> AsyncGenerator[str, None]:
        # render complete component with processssing
        complete_template = template("list/list_complete.html")
        yield complete_template.render(items=self.items)

    async def render(
        self, response_stream: AsyncGenerator[str, None], **kwargs
    ) -> AsyncGenerator[str, None]:
        # render the component in 3 stages

        async for item in self.placeholder_render(**kwargs):
            yield item
            await asyncio.sleep(0.25)
        async for item in self.partial_render(response_stream, **kwargs):
            yield item
            await asyncio.sleep(0.1)
        async for item in self.complete_render(**kwargs):
            yield item


@dataclass
class FormComponent(AbstractComponent):
    form: List[Dict[str, str]] = field(default_factory=list)
    output: str = field(default="html")  # either output html or incremental json

    async def placeholder_render(self, **kwargs) -> AsyncGenerator[str, None]:
        placeholder_template = template("form/form_placeholder.html")
        template_wrapper = template("form/form_container.html")
        component_html = placeholder_template.render()
        yield template_wrapper.render(form_content=component_html)

    async def partial_render(
        self,
        response_stream: AsyncGenerator[str, None],
        FormType=DefaultFormStruct,
        FormFieldType=DefaultFormItem,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        partial_template = template("form/form_partial.html")
        template_wrapper = template("form/form_container.html")

        # should probably be user input...
        start_key = get_struct_keys(FormType)[0]  # should only have one key
        field_name_key = get_struct_keys(FormFieldType)[
            0
        ]  # should only have one item key
        field_description_key = get_struct_keys(FormFieldType)[1]

        form_items_response: AsyncGenerator = parse_form_json_ts(
            response_stream,
            start_key=start_key,
            field_name_key=field_name_key,
            field_description_key=field_description_key,
        )

        async for streamed_items in form_items_response:
            streamed_list = [streamed_items[i] for i in sorted(streamed_items.keys())]
            self.form = streamed_list
            patial_template_html = partial_template.render(form=list(streamed_list))
            yield template_wrapper.render(form_content=patial_template_html)

    async def complete_render(self, **kwargs) -> AsyncGenerator[str, None]:
        # render complete component with processssing
        complete_template = template("form/form_complete.html")
        yield complete_template.render(form=self.form)

    async def render(
        self, response_stream: AsyncGenerator[str, None], **kwargs
    ) -> AsyncGenerator[str, None]:
        # render the component in 3 stages

        async for item in self.placeholder_render(**kwargs):
            yield item
            await asyncio.sleep(0.25)
        async for item in self.partial_render(response_stream, **kwargs):
            yield item
            await asyncio.sleep(0.05)
        async for item in self.complete_render(**kwargs):
            yield item


@dataclass
class TableComponent(AbstractComponent):
    table: List[Dict[str, str]] = field(default_factory=list)
    output: str = field(default="html")  # either output html or incremental json

    async def placeholder_render(self, **kwargs) -> AsyncGenerator[str, None]:
        placeholder_template = template("table/table_placeholder.html")
        template_wrapper = template("table/table_container.html")
        component_html = placeholder_template.render()
        yield template_wrapper.render(table_content=component_html)

    
    async def partial_render(
        self,
        response_stream: AsyncGenerator[str, None],
        RowType=ExampleRow,
        TableType=ExampleTableStruct,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        partial_template = template("table/table_partial.html")
        template_wrapper = template("table/table_container.html")

        form_items_response: AsyncGenerator = parse_table_json_ts(
            response_stream,
            row_struct = RowType
        )

        async for streamed_items in form_items_response:
            streamed_list = [streamed_items[i] for i in sorted(streamed_items.keys())]
            self.table = streamed_list
            patial_template_html = partial_template.render(table=list(streamed_list))
            yield template_wrapper.render(table_content=patial_template_html)

    async def complete_render(self, **kwargs) -> AsyncGenerator[str, None]:
        # render complete component with processssing
        complete_template = template("table/table_complete.html")
        yield complete_template.render(table=self.table)

    async def render(
        self, response_stream: AsyncGenerator[str, None], **kwargs
    ) -> AsyncGenerator[str, None]:
        # render the component in 3 stages

        async for item in self.placeholder_render(**kwargs):
            yield item
            await asyncio.sleep(0.25)
        async for item in self.partial_render(response_stream, **kwargs):
            yield item
            await asyncio.sleep(0.05)
        async for item in self.complete_render(**kwargs):
            yield item