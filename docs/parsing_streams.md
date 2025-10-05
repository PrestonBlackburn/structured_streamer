# Technical Implementation

The library relies heavliy on the tree sitter and tree sitter python bindings for efficient parsing. I tried a couple simpler parsing approaches at first, and it quickly realized that it is a complex problem, and tree sitter has already been built by much smarter people to handle these complexities. Since we are working with structured text streams, our use cases overlap nicely with the text editor use case that tree sitter is primarily built for.   

Tree Sitter Docs: https://tree-sitter.github.io/tree-sitter/  

## Parsing

The goal of the parsing is to always output fully constructed python structures. This means that all python structures must have default values that will be returned when there are no matching nodes in the parse tree. You can checkout the `/src/struct_strm/structs/` folder for examples of what kind of structures are expected, and examples of streams for those components.   

In the trivial case of a structured list, the structures may look like:
```python
class PydanticDefaultListItem(BaseModel):
    item: str = ""


class PydanticDefaultListStruct(BaseModel):
    # mostly just for testing
    items: list[DefaultListItem] = []
```

The structures can then be used both for the OpenAI request and the parsing method from this library. Since the whole point of this library is to stream responses, async + generators are the supported response types. For each itteration a new instance of the passed structure (`DefaultListStruct` in this case) is returned. Not the most efficient, but hey this is Python. The heavy duty processing is handled efficeintly by tree sitter.

```python
list_items_response: AsyncGenerator[DefaultListStruct, None] = tree_sitter_parse(
    DefaultListStruct,
    response_stream,
)
```

The response for this parsed example would look something like:
```markdown
>>> DefaultListStruct(items=[])
>>> DefaultListStruct(items=[DefaultListItem(item="apple"),])
>>> DefaultListStruct(items=[DefaultListItem(item="apple orange strawberry"),])
>>> DefaultListStruct(items=[DefaultListItem(item="apple orange strawberry"), DefaultListItem(item="banana")])
>>> DefaultListStruct(items=[DefaultListItem(item="apple orange strawberry"), DefaultListItem(item="banana kiwi grape")])
>>> etc...
```


## UI Integration

Most of my examples are tested with HTMX, since it is easy to setup in a simple python project for testing. I imagine most users will dump the results to json format for use with front ends like React. 
