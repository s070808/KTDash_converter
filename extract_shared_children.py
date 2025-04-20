import json
from pathlib import Path
from collections import defaultdict

def extract_and_flatten_shared_children(data, parent_key, child_key, output_key):
    """
    Extracts all `child_key` lists under `parent_key` entries in the JSON
    and places them into a top-level key `output_key`.
    """
    flattened = []

    if parent_key in data:
        for entry in data[parent_key]:
            if isinstance(entry, dict) and child_key in entry:
                flattened.extend(entry[child_key])

    data[output_key] = flattened
    return data

def recursive_flatten(data, keys_to_flatten):
    """
    Takes a dictionary `keys_to_flatten` in the form:
    { "parent_key": ["child_key1", "child_key2"] }
    and flattens all child keys from each parent.
    """
    for parent_key, children in keys_to_flatten.items():
        for child_key in children:
            output_key = f"{parent_key}_{child_key}"
            extract_and_flatten_shared_children(data, parent_key, child_key, output_key)
    return data

# === Load pretty JSON ===
input_path = "pretty_output.json"
output_path = "flattened_output.json"

with open(input_path, "r", encoding="utf-8") as f:
    json_data = json.load(f)

# === Define what to flatten ===
# You can add more as needed
keys_to_flatten = {
    "fireteams": ["operatives"],
    "operatives": ["abilities", "weapons", "uniqueactions"]
}

# === Apply flattening ===
flattened = recursive_flatten(json_data, keys_to_flatten)

# === Save output ===
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(flattened, f, indent=4)

print(f"✅ Flattened JSON written to {output_path}")
