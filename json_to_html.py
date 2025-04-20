import json
from pathlib import Path
from html import escape

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
    "    th, td { border: 1px solid #333; padding: 8px; text-align: left; }",
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

# Helper to render a table from a list of dicts
def render_table(title, items):
    if not items:
        return f"<h2>{title}</h2><p><em>No data</em></p>"

    headers = sorted({key for item in items for key in item})
    table_html = [f"<h2>{escape(title)}</h2>", "<table>"]
    table_html.append("<tr>" + "".join(f"<th>{escape(h)}</th>" for h in headers) + "</tr>")
    for item in items:
        table_html.append("<tr>" + "".join(f"<td>{escape(str(item.get(h, '')))}</td>" for h in headers) + "</tr>")
    table_html.append("</table>")
    return "\n".join(table_html)

# Render content
for key, value in data.items():
    if isinstance(value, list) and all(isinstance(i, dict) for i in value):
        html_parts.append(render_table(key, value))
    elif isinstance(value, list):
        html_parts.append(f"<h2>{escape(key)}</h2><pre>{escape(json.dumps(value, indent=2))}</pre>")
    elif isinstance(value, dict):
        html_parts.append(f"<h2>{escape(key)}</h2><pre>{escape(json.dumps(value, indent=2))}</pre>")
    else:
        html_parts.append(f"<h2>{escape(key)}</h2><p>{escape(str(value))}</p>")

# Close it off
html_parts.append("</body></html>")

# Write to file
Path("flattened_output_viewer.html").write_text("\n".join(html_parts), encoding="utf-8")
print("🌑 Dark-themed HTML viewer created as 'flattened_output_viewer.html'")
