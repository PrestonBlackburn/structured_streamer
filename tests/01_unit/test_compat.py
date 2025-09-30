from struct_strm.compat import to_dict, to_json, is_pydantic_model
from dataclasses import dataclass
from pydantic import BaseModel
from struct_strm.structs.form_structs import DefaultFormItem, DefaultFormStruct


class PydanticExample(BaseModel):
    example: str = "example"


@dataclass
class DataclassExample:
    example: str = "example"


list_struct = DefaultFormStruct(
    form_fields=[
        DefaultFormItem(
            field_name="fruits", field_placeholder="apple &orange &straw&berry"
        ),
        DefaultFormItem(
            field_name="appliance", field_placeholder="blender &mixer &toaster"
        ),
        DefaultFormItem(field_name="dishes", field_placeholder="plate &bowl"),
    ]
)


def test_pydantic_model_check():
    pd_example = PydanticExample()
    is_pydantic = is_pydantic_model(pd_example)
    assert is_pydantic == True


def test_negative_pydantic_model_check():
    dc_example = DataclassExample()
    is_pydantic = is_pydantic_model(dc_example)
    assert is_pydantic == False


def test_none_pydantic_model_check():
    is_pydantic = is_pydantic_model(None)
    assert is_pydantic == False


def test_type_default_form_struct_instance():
    is_pydantic = is_pydantic_model(list_struct)
    assert is_pydantic == True


def test_type_default_form_struct():
    is_pydantic = is_pydantic_model(DefaultFormStruct)
    assert is_pydantic == True


def test_dc_to_json():
    test_json = to_json(DataclassExample())
    assert test_json.strip() == '{"example": "example"}'.strip()


def test_pd_to_json():
    test_json = to_json(PydanticExample())
    assert test_json.strip() == '{"example":"example"}'.strip()


def test_dc_to_dict():
    test_dict = to_dict(DataclassExample())
    assert test_dict == {"example": "example"}


def test_pd_to_dict():
    test_dict = to_dict(PydanticExample())
    assert test_dict == {"example": "example"}
