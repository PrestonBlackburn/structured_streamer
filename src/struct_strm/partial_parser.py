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
    items: List[str] = []
    item_idx = -1
    item_values: Dict[int, str] = {}

    async for chunk in response_stream:
        chunk = chunk.strip()

        if not chunk:
            continue

        buffer += chunk + " "

        if not inside_items and start_key in buffer:
            inside_items = True
            buffer = buffer.split(start_key, 1)[1]
            continue

        if inside_items:
            if not inside_item:
                if f'"{item_key}"' in buffer or f"{item_key}" in buffer:
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
                if chunk in {"}", "]", "},"}:
                    inside_item = False
                    continue

                # Stream token into current item value
                if chunk not in {":", '"', "'", ","}:
                    current_item_value += chunk + " "
                    clean = current_item_value.strip().strip('"').strip(",")
                    if item_values.get(item_idx) != clean:
                        item_values[item_idx] = clean
                        yield [item_values[i] for i in sorted(item_values.keys())]
