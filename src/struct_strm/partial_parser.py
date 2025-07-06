from typing import AsyncGenerator, List, Dict



async def inside_start_key(buffer:str) -> bool:
    end_token = ""

    return bool


async def inside_item_key(buffer:str) -> bool:
    end_token = ""


    return

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



async def parse_list_json_updated(
    response_stream: AsyncGenerator[str, None],
    start_key: str = "items",
    item_key: str = "item",
) -> AsyncGenerator[List[str], None]:
    buffer = ""
    inside_items = False
    inside_item = False
    capturing_value = False
    escape_next = False

    item_idx = -1
    current_item_value = ""
    item_values: Dict[int, str] = {}

    async for chunk in response_stream:
        buffer += chunk

        i = 0
        while i < len(buffer):
            char = buffer[i]

            if not inside_items:
                if start_key in buffer:
                    inside_items = True
                    # Skip ahead to the part after the array start `[...]`
                    idx = buffer.find('[')
                    if idx != -1:
                        buffer = buffer[idx + 1 :]
                        i = 0
                        continue
                    else:
                        buffer = ""
                        break
                else:
                    # Still waiting for the items key
                    break

            # Find start of a new object
            if not inside_item and char == "{":
                inside_item = True
                current_item_value = ""
                i += 1
                continue

            # Look for "item" key
            if inside_item and not capturing_value:
                if buffer[i:].startswith(f'"{item_key}"'):
                    # Move past `"item"` and optional `:`
                    end_idx = buffer.find(":", i + len(item_key) + 2)
                    if end_idx != -1:
                        i = end_idx + 1
                        # Look for opening quote of value
                        while i < len(buffer) and buffer[i] != '"':
                            i += 1
                        if i < len(buffer) and buffer[i] == '"':
                            capturing_value = True
                            i += 1
                        continue
                    else:
                        break  # Wait for more chars
                else:
                    i += 1
                    continue

            # Capture value
            elif inside_item and capturing_value:
                if escape_next:
                    current_item_value += char
                    escape_next = False
                elif char == "\\":
                    escape_next = True
                elif char == '"':
                    # End of value
                    item_idx += 1
                    clean = current_item_value.strip()
                    item_values[item_idx] = clean
                    yield [item_values[i] for i in sorted(item_values)]
                    # Reset state
                    inside_item = False
                    capturing_value = False
                    current_item_value = ""
                else:
                    current_item_value += char
                i += 1
                continue
            else:
                i += 1

        buffer = ""  # Reset buffer each round after processing