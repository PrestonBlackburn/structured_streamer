from typing import AsyncGenerator, List, Dict


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


async def parse_form_json(
    response_stream, 
    start_key: str= "form_fields", 
    field_name_key: str = "field_name", 
    field_description_key: str = "field_placeholder"
) -> AsyncGenerator[List[Dict[str, str]], None]:

    # where "field" refers to name + description pair
    buffer = ""
    inside_fields = False
    inside_field_pair = False
    inside_field_name = False
    inside_field_desc = False

    current_name_field_value = ""
    current_desc_field_value = ""
    field_idx = -1
    # return list of dicts where each dict needs:
    # {idx: {field_name_key: "...", field_desc_key: "..."}, idx: {field_name_key: "...", field_desc_key: "..."}, etc...}
    field_values: Dict[int, Dict[str, str]] = {}

    async for chunk in response_stream:
        if not chunk:
            continue

        buffer += chunk

        if not inside_fields and f'"{start_key}":' in buffer:
            
            inside_fields = True
            # start getting the content
            buffer = buffer.split(start_key, 1)[1]
            continue

        if inside_fields:
            # this most likely will come first?
            if not inside_field_pair:
                if f'"{field_name_key}":' in buffer:
                    inside_field_pair = True
                    inside_field_name = True
                    inside_field_desc = False
                    current_name_field_value = ""
                    field_idx += 1
                    after_key = buffer.split(field_name_key, 1)[1]
                    if ":" in after_key:
                        buffer = after_key.split(":", 1)[1]
                    else:
                        buffer = ""
                    continue

                if f'"{field_description_key}":' in buffer:
                    inside_field_pair = True
                    inside_field_name = False
                    inside_field_desc = True
                    current_desc_field_value = ""
                    after_key = buffer.split(field_name_key, 1)[1]
                    if ":" in after_key:
                        buffer = after_key.split(":", 1)[1]
                    else:
                        buffer = ""
                    continue


            if inside_field_pair:
                if chunk in {"}", "]", "},", '},{"'}:
                    inside_field_pair = False
                    field_name_clean = ""
                    field_desc_clean = ""
                    continue

                # Stream token into current item value
                # if chunk not in {":", '"', "'", ","}:
                if chunk not in {'"', "'", ","}:
                    if inside_field_name:
                        current_name_field_value += chunk
                        field_name_clean = current_name_field_value.strip().strip('"').strip(",")
                    if inside_field_desc:
                        current_desc_field_value += chunk
                        field_desc_clean = current_desc_field_value.strip().strip('"').strip(",")

                    clean = {field_name_key: field_name_clean, field_description_key: field_desc_clean}
                    # compare str to avoid pointers
                    if str(field_values.get(field_idx)) != str(clean):
                        field_values[field_idx] = {field_name_key: field_name_clean, field_description_key: field_desc_clean}
                        yield [ 
                            {
                                field_name_key:field_values[i][field_name_key], 
                                field_description_key:field_values[i][field_description_key]
                            } for i in sorted(field_values.keys())
                        ]
