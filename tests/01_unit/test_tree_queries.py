import asyncio
from struct_strm.tree_queries import (
    get_str_keys,
    get_query_l1,
    get_query_l2,
    get_queries,
    has_nested_structure,
)
import pytest
from pydantic import BaseModel
from dataclasses import dataclass, field
from typing import Any


@pytest.fixture
def item_dataclass():
    @dataclass
    class Item:
        sku: str = ""

    return Item


@pytest.fixture
def item_pydantic_model():
    class Item(BaseModel):
        sku: str = ""

    return Item


@pytest.fixture
def product_dataclass(item_dataclass):
    Item: type[Any] = item_dataclass

    @dataclass
    class Product:
        product_id: str = ""
        name: str = ""
        price: str = ""
        items: list[Item] = field(default_factory=lambda: [Item()])

    return Product


@pytest.fixture
def product_pydantic_model(item_pydantic_model):
    Item: BaseModel = item_pydantic_model

    class Product(BaseModel):
        product_id: str = ""
        name: str = ""
        price: str = ""
        items: list[Item] = [Item()]

    return Product

@pytest.fixture
def profile_with_all_types_pydantic():
    class Profile(BaseModel):
        name: str
        age: int
        is_active: bool
        score: float
        items: list[str] # This should be ignored by the primitive key search
    return Profile

def test_get_str_keys_dataclass(product_dataclass):
    Product = product_dataclass
    keys = asyncio.run(get_str_keys(Product))
    for key in ["product_id", "name", "price"]:
        assert key in keys
    assert "items" not in keys


def test_get_str_keys_pydantic(product_pydantic_model):
    Product = product_pydantic_model
    keys = asyncio.run(get_str_keys(Product))
    for key in ["product_id", "name", "price"]:
        assert key in keys
    assert "items" not in keys


def test_get_l1_query_dataclass(product_dataclass):

    Product = product_dataclass

    l1_query = asyncio.run(get_query_l1(Product))
    expected_query_str = f"""(
        (pair
            key: (string) @key
            value: (_value) @value)
        (#any-of? @key "\\"product_id\\"" "\\"name\\"" "\\"price\\"")
        )
    """

    assert l1_query.replace(" ", "") == expected_query_str.replace(" ", "")


def test_get_l2_query_dataclass(product_dataclass):

    Product = product_dataclass
    l2_query = asyncio.run(get_query_l2(Product, group_by_object=True))
    expected_query_str = """(
        (object
        (pair
            key: (string) @key
            value: (_value) @value)
        (#not-eq? @key "\\"product_id\\"")
        (#not-eq? @key "\\"name\\"")
        (#not-eq? @key "\\"price\\"")
        (#any-of? @key "\\"sku\\"")
    )) @obj
    """
    assert l2_query["items"]["query_str"].replace(
        " ", ""
    ) == expected_query_str.replace(" ", "")

def test_get_l2_query_dataclass_ungrouped(product_dataclass):

    Product = product_dataclass
    l2_query = asyncio.run(get_query_l2(Product, group_by_object=False))
    expected_query_str = """(
        (pair
            key: (string) @key
            value: (_value) @value)
        (#not-eq? @key "\\"product_id\\"")
        (#not-eq? @key "\\"name\\"")
        (#not-eq? @key "\\"price\\"")
        (#any-of? @key "\\"sku\\"")
    )
    """
    assert l2_query["items"]["query_str"].replace(
        " ", ""
    ) == expected_query_str.replace(" ", "")

def test_get_l1_query_pydantic(product_pydantic_model):

    Product = product_pydantic_model
    l1_query = asyncio.run(get_query_l1(Product))
    expected_query_str = f"""(
        (pair
            key: (string) @key
            value: (_value) @value)
        (#any-of? @key "\\"product_id\\"" "\\"name\\"" "\\"price\\"")
        )
    """
    assert l1_query.replace(" ", "") == expected_query_str.replace(" ", "")


def test_get_l2_query_pydantic(product_pydantic_model):

    Product = product_pydantic_model
    l2_query = asyncio.run(get_query_l2(Product, group_by_object=True))
    expected_query_str = """(
        (object
        (pair
            key: (string) @key
            value: (_value) @value)
        (#not-eq? @key "\\"product_id\\"")
        (#not-eq? @key "\\"name\\"")
        (#not-eq? @key "\\"price\\"")
        (#any-of? @key "\\"sku\\"")
    )) @obj
    """
    assert l2_query["items"]["query_str"].replace(
        " ", ""
    ) == expected_query_str.replace(" ", "")

def test_get_l2_query_pydantic_ungrouped(product_pydantic_model):

    Product = product_pydantic_model
    l2_query = asyncio.run(get_query_l2(Product, group_by_object=False))
    expected_query_str = """(
        (pair
            key: (string) @key
            value: (_value) @value)
        (#not-eq? @key "\\"product_id\\"")
        (#not-eq? @key "\\"name\\"")
        (#not-eq? @key "\\"price\\"")
        (#any-of? @key "\\"sku\\"")
    )
    """
    assert l2_query["items"]["query_str"].replace(
        " ", ""
    ) == expected_query_str.replace(" ", "")



def test_has_nested_struct_dataclass(product_dataclass):
    Product = product_dataclass
    nested_struct = asyncio.run(has_nested_structure(Product))
    assert nested_struct == True


def test_has_nested_struct_pydantic(product_pydantic_model):
    Product = product_pydantic_model
    nested_struct = asyncio.run(has_nested_structure(Product))
    assert nested_struct == True


def test_not_has_nested_struct_dataclass(item_dataclass):
    Item = item_dataclass
    nested_struct = asyncio.run(has_nested_structure(Item))
    assert nested_struct == False


def test_not_has_nested_struct_dataclas(item_pydantic_model):
    Item = item_pydantic_model
    nested_struct = asyncio.run(has_nested_structure(Item))
    assert nested_struct == False


def test_get_queries_dataclass(product_dataclass):
    Product = product_dataclass
    l1_query, l2_query = asyncio.run(get_queries(Product, group_by_object=True))
    expected_query_str_l1 = f"""(
        (pair
            key: (string) @key
            value: (_value) @value)
        (#any-of? @key "\\"product_id\\"" "\\"name\\"" "\\"price\\"")
        )
    """
    expected_query_str_l2 = """(
        (object
        (pair
            key: (string) @key
            value: (_value) @value)
        (#not-eq? @key "\\"product_id\\"")
        (#not-eq? @key "\\"name\\"")
        (#not-eq? @key "\\"price\\"")
        (#any-of? @key "\\"sku\\"")
    )) @obj
    """
    assert l1_query is not None
    assert l2_query is not None
    assert l1_query.replace(" ", "") == expected_query_str_l1.replace(" ", "")
    assert l2_query["items"]["query_str"].replace(
        " ", ""
    ) == expected_query_str_l2.replace(" ", "")


def test_get_queries_pydantic(product_pydantic_model):
    Product = product_pydantic_model
    l1_query, l2_query = asyncio.run(get_queries(Product, group_by_object=True))
    expected_query_str_l2 = """(
        (object
        (pair
            key: (string) @key
            value: (_value) @value)
        (#not-eq? @key "\\"product_id\\"")
        (#not-eq? @key "\\"name\\"")
        (#not-eq? @key "\\"price\\"")
        (#any-of? @key "\\"sku\\"")
    )) @obj
    """
    #in this ive replaced string -> _value wrt the grammer 
    expected_query_str_l1 = f"""(
        (pair
            key: (string) @key
            value: (_value) @value)
        (#any-of? @key "\\"product_id\\"" "\\"name\\"" "\\"price\\"")
        )
    """
    assert l1_query is not None
    assert l2_query is not None
    assert l1_query.replace(" ", "") == expected_query_str_l1.replace(" ", "")
    assert l2_query["items"]["query_str"].replace(
        " ", ""
    ) == expected_query_str_l2.replace(" ", "")


def test_replaced_str_keys_pydantic(profile_with_all_types_pydantic):
    Profile = profile_with_all_types_pydantic
    from struct_strm.tree_queries import get_str_keys
    
    keys = asyncio.run(get_str_keys(Profile))
    
    # Assert that all primitive types are found
    for key in ["name", "age", "is_active", "score"]:
        assert key in keys
        
    # Assert that the list is NOT included
    assert "items" not in keys


# Add this function to the end of the file
def test_get_l1_query_with_all_types(profile_with_all_types_pydantic):
    Profile = profile_with_all_types_pydantic

    l1_query = asyncio.run(get_query_l1(Profile))
    
    # Note the value is now (_value) instead of (string)
    expected_query_str = f"""(
        (pair
            key: (string) @key
            value: (_value) @value)  
        (#any-of? @key "\\"name\\"" "\\"age\\"" "\\"is_active\\"" "\\"score\\"")
        )
    """
    
    # The .replace() helps ignore whitespace differences
    assert l1_query.replace(" ", "").replace("\n", "") == expected_query_str.replace(" ", "").replace("\n", "")