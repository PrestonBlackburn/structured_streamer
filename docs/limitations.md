# Limitations

There are still many limiations for the parsing that I'm working to address. The current setup works for my use cases, but is far from ideal. Some limitations include:
### 1. Only flat structs, or structs with up to one nextested level are supported  
Suported:
```python
class DefaultListItem(BaseModel):
    item: str = ""


class DefaultListStruct(BaseModel):
    # mostly just for testing
    items: list[DefaultListItem] = []
```
Not supported yet:  
```python
class DefaultListItemDetail(BaseModel):
    detail: str = ""

class DefaultListItem(BaseModel):
    item: DefaultListItemDetail = ""

class DefaultListStruct(BaseModel):
    # mostly just for testing
    items: list[DefaultListItem] = []
```
### 2. I'm not handling any data types beyond strings and arrays (no ints/floats or optional types)  
Suported:  
```python
class DefaultListItem(BaseModel):
    item: str = ""
```
Not supported yet:
```python
class DefaultListItem(BaseModel):
    item: int = ""
```
### 3. Nested structures must have different value names  
Suported:
```python
class DefaultListItem(BaseModel):
    item: str = ""

class DefaultListStruct(BaseModel):
    # mostly just for testing
    items: list[DefaultListItem] = []
```
Not supported yet:
```python
class DefaultListItem(BaseModel):
    items: str = ""

class DefaultListStruct(BaseModel):
    # mostly just for testing
    items: list[DefaultListItem] = []
```
### 4. I'm in the process of adding support for dataclasses
Currenlty pydantic models are the only structures supported