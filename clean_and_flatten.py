import json
from pathlib import Path


def remove_keys(data, keys_to_ignore):
    for key in keys_to_ignore:
        if key in data:
            del data[key]
    return data


def find_and_flatten(data, target_key, child_key):
    """
    Recursively find all dictionaries with key `target_key`, and if their value
    is a list of dicts that contain `child_key`, collect all such child_key values.
    """
    found = []

    def recurse(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == target_key and isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict) and child_key in item:
                            found.extend(item[child_key])
                else:
                    recurse(value)
        elif isinstance(obj, list):
            for item in obj:
                recurse(item)

    recurse(data)
    return found


def flatten_all(data, targets):
    """
    targets = {
        "operatives": ["abilities", "weapons", "uniqueactions"]
    }
    """
    def deduplicate_by_key(items, key):
        seen = set()
        deduped = []
        for item in items:
            identifier = item.get(key)
            if identifier and identifier not in seen:
                seen.add(identifier)
                deduped.append(item)
        return deduped

    # Map child_key to the key used for deduplication
    deduplication_keys = {
        "abilities": "title",
        "weapons": "wepname",
        "uniqueactions": "title"  # Adjust if you find the actual key used
    }

    for target_key, children in targets.items():
        for child_key in children:
            flattened_key = f"{target_key}_{child_key}"
            collected = find_and_flatten(data, target_key, child_key)

            # Deduplicate if we know how
            dedup_key = deduplication_keys.get(child_key)
            if dedup_key:
                collected = deduplicate_by_key(collected, dedup_key)

            data[flattened_key] = collected
    return data



# === Configuration ===
input_path = "pretty_output.json"
intermediate_path = "cleaned_output.json"
final_output_path = "flattened_output.json"

# Keys to remove from top level
keys_to_ignore = ["rosters"]

# Nested keys to flatten recursively
flatten_targets = {
    "operatives": ["abilities", "weapons", "uniqueactions"],
    "fireteams": ["operatives"]
}

# === Load original JSON ===
with open(input_path, "r", encoding="utf-8") as f:
    json_data = json.load(f)

# === Step 1: Remove unwanted keys ===
cleaned_data = remove_keys(json_data, keys_to_ignore)
with open(intermediate_path, "w", encoding="utf-8") as f:
    json.dump(cleaned_data, f, indent=4)
print(f"🧹 Cleaned JSON written to {intermediate_path} (without: {', '.join(keys_to_ignore)})")

# === Step 2: Flatten deeply nested shared children ===
flattened_data = flatten_all(cleaned_data, flatten_targets)
with open(final_output_path, "w", encoding="utf-8") as f:
    json.dump(flattened_data, f, indent=4)
print(f"📦 Deep-flattened JSON written to {final_output_path}")
