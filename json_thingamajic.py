import json
import html
from pathlib import Path

# Paste the killteam blob including killteam="..."
html_encoded_raw = r"""
killteam="{&quot;factionid&quot;:&quot;HBR&quot;}"
""".strip()

# Step 1: Extract actual JSON value from killteam="..."
if html_encoded_raw.startswith("killteam="):
    # Strip prefix and surrounding quotes
    html_encoded_json = html_encoded_raw[len("killteam="):].strip().strip('"')
else:
    html_encoded_json = html_encoded_raw

# Step 2: Unescape HTML entities
decoded_json_str = html.unescape(html_encoded_json)

# Step 3: Parse JSON
try:
    data = json.loads(decoded_json_str)
except json.JSONDecodeError as e:
    print("❌ JSON parsing failed:")
    print(e)
    exit(1)

# Step 4: Pretty-print JSON to file
pretty_json = json.dumps(data, indent=4)
Path("pretty_output.json").write_text(pretty_json, encoding="utf-8")
print("✔️ Pretty JSON written to 'pretty_output.json'.")
