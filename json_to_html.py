import json
from pathlib import Path
from html import escape
import re

# Keys to ignore at the top level
BLACKLIST_KEYS = {"fireteams", "operatives_weapons"}  # top-level
BLACKLIST_FIELDS = {
    "factionid", "killteamid", "ployid", "ploytype", "eqcategory", "eqid",
    "eqvar1", "eqvar2", "eqvar3", "eqvar4", "fireteamid", "opid","eqpts",
    "eqseq","edition","tacopid","tacopseq","abilityid","isdefault",
    "isselected","wepid","wepseq"
}


# Load the flattened JSON
with open("flattened_output.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Start HTML
html_parts = [
    "<!DOCTYPE html>",
    "<html>",
    "<head>",
    "  <meta charset='UTF-8'>",
    "  <title>Flattened JSON Viewer</title>",
    "  <style>",
    "    body { background: #1e1e1e; color: #d4d4d4; font-family: 'Segoe UI', sans-serif; padding: 2em; }",
    "    h1, h2 { color: #61dafb; }",
    "    table { border-collapse: collapse; width: 100%; margin-bottom: 2em; }",
    "    th, td { border: 1px solid #333; padding: 8px; text-align: left; vertical-align: top; }",
    "    th { background-color: #333; color: #ffffff; }",
    "    tr:nth-child(even) { background-color: #2a2a2a; }",
    "    tr:nth-child(odd) { background-color: #252526; }",
    "    pre { background: #2d2d2d; padding: 1em; border-radius: 6px; overflow-x: auto; white-space: pre-wrap; }",
    "    a { color: #61dafb; }",
    "  </style>",
    "</head>",
    "<body>",
    "  <h1>Flattened JSON Viewer</h1>"
]

import re

def contains_html(s):
    return bool(re.search(r"</?[a-z][\s\S]*?>", s, re.IGNORECASE))

def render_table(title, items):
    if not items:
        return f"<h2>{escape(title)}</h2><p><em>No data</em></p>"

    headers = sorted({key for item in items for key in item if key not in BLACKLIST_FIELDS})
    table_html = [f"<h2>{escape(title)}</h2>", "<table>"]
    table_html.append("<tr>" + "".join(f"<th>{escape(h)}</th>" for h in headers) + "</tr>")

    for item in items:
        row = []
        for h in headers:
            val = item.get(h, "")
            if isinstance(val, list) and all(isinstance(sub, dict) for sub in val):
                # Render inner table for list of dicts
                inner_table = ["<table>"]
                inner_headers = sorted({k for d in val for k in d})
                inner_table.append("<tr>" + "".join(f"<th>{escape(k)}</th>" for k in inner_headers) + "</tr>")
                for d in val:
                    inner_table.append("<tr>" + "".join(
                        f"<td>{escape(str(d.get(k, '')))}</td>" for k in inner_headers
                    ) + "</tr>")
                inner_table.append("</table>")
                row.append(f"<td>{''.join(inner_table)}</td>")
            elif isinstance(val, str) and contains_html(val):
                row.append(f"<td>{val}</td>")
            else:
                row.append(f"<td>{escape(str(val))}</td>")
        table_html.append("<tr>" + "".join(row) + "</tr>")

    table_html.append("</table>")
    return "\n".join(table_html)



# Recursively render any dict/list combo
def render_value(key, value):
    if isinstance(value, list) and all(isinstance(i, dict) for i in value):
        return render_table(key, value)
    elif isinstance(value, dict):
        return "\n".join(
            render_value(f"{key} - {k}", v)
            for k, v in value.items()
            if k not in BLACKLIST_FIELDS
        )
    elif isinstance(value, str) and contains_html(value):
        return f"<h2>{escape(key)}</h2><div>{value}</div>"  # render embedded HTML
    else:
        return f"<h2>{escape(key)}</h2><pre>{escape(str(value))}</pre>"


# Render all top-level keys
for key, value in data.items():
    if key in BLACKLIST_KEYS:
        continue  # Skip keys in the blacklist
    if isinstance(value, list):
        html_parts.append(render_table(key, value))
    elif isinstance(value, dict):
        for subkey, subval in value.items():
            if isinstance(subval, list):
                html_parts.append(render_table(f"{key}_{subkey}", subval))

# Finalize
html_parts.append("</body></html>")
Path("flattened_output_viewer.html").write_text("\n".join(html_parts), encoding="utf-8")
print("✅ HTML viewer created: flattened_output_viewer.html (with proper nested support)")
