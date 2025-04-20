import json
from pathlib import Path
from html import escape
import re

# === CONFIGURATION ===

BLACKLIST_KEYS = {"fireteams", "operatives_weapons", "customkeyword", "killteamname"}
BLACKLIST_FIELDS = {
    "factionid", "killteamid", "ployid", "ploytype", "eqcategory", "eqid", "eqvar1", "eqvar2", "eqvar3", "eqvar4",
    "fireteamid", "opid", "eqpts", "eqseq", "edition", "tacopid", "tacopseq", "abilityid", "isdefault",
    "isselected", "wepid", "wepseq", "eqtype", "weapon", "name", "profileid"
}

COLUMN_CONFIG = {
    "strat": [
        ("ployname", "Name", "w20"),       # Short name
        ("CP", "CP", "w5"),               # Small number
        ("description", "Description", "w75")  # Most of the space
    ],
    "tac": [
        ("ployname", "Name", "w20"),
        ("CP", "CP", "w5"),
        ("description", "Description", "w75")
    ],
    "equipments": [
        ("eqname", "Name", "w25"),         # Can be slightly longer
        ("eqdescription", "Description", "w75")
    ],
    "tacops": [
        ("title", "Title", "w25"),         # Brief, but longer than a name
        ("description", "Description", "w75")
    ],
    "operatives_abilities": [              # Faction Rules
        ("title", "Title", "w20"),         # Often a short phrase
        ("description", "Description", "w80")
    ],
    "weapons": [
        ("wepname", "Weapon", "w15"),      # Longer names like "Shuriken Catapult"
        ("weptype", "Ranged/Melee", "w10"),# Short tag
        ("profiles", "Profiles", "w75")    # Table goes here, needs width
    ],
    "abilities": [
        ("title", "Title", "w20"),
        ("description", "Description", "w80")
    ]
}

TITLE_OVERRIDES = {
    "strat": "Strategic Ploys",
    "tac": "Tactical Ploys",
    "killteamname": "Kill Team",
    "description": "Description",
    "equipments": "Equipment",
    "killteamcomp": "Operatives",
    "tacops": "TacOps",
    "operatives_abilities": "Faction Rules",
    "operatives_uniqueactions": "Unique Actions for Operatives",
    "fireteams_operatives": "Operatives",
    "ploys": "Ploys"
}

EMPHASIZE_FIELDS = {
    "equipments": ("eqname", "eqtype"),
    "tacops": ("title", "archetype"),
}

SKIP_RENDER_KEYS = {"weapons", "abilities", "uniqueactions"}
RENDER_ORDER = ["description", "killteamcomp","operatives_abilities", "fireteams_operatives", "ploys", "equipments", "tacops"]

# === UTILITY ===

def title_for(key):
    return TITLE_OVERRIDES.get(key.lower(), key)

def should_skip_key(key):
    return key in BLACKLIST_FIELDS or key in SKIP_RENDER_KEYS

def contains_html(s):
    return bool(re.search(r"</?[a-z][\s\S]*?>", s, re.IGNORECASE))

def render_subtable(items):
    headers = sorted({k for d in items for k in d if k not in BLACKLIST_FIELDS})
    html = ["<table>"]
    html.append("<tr>" + "".join(f"<th>{escape(h)}</th>" for h in headers) + "</tr>")
    for d in items:
        html.append("<tr>" + "".join(f"<td>{escape(str(d.get(h, '')))}</td>" for h in headers) + "</tr>")
    html.append("</table>")
    return "".join(html)

# === RENDERING ===

def render_table(title, items, add_header=True):
    if not items:
        return f"<h2>{escape(title_for(title))}</h2><p><em>No data</em></p>"

    pretty_title = title_for(title)

    if title.lower() in COLUMN_CONFIG:
        ordered_headers = [field for field, *_ in COLUMN_CONFIG[title.lower()]]
        header_labels = [label for _, label, *_ in COLUMN_CONFIG[title.lower()]]
        column_classes = [col[2] if len(col) > 2 else "" for col in COLUMN_CONFIG[title.lower()]]
    else:
        ordered_headers = sorted({key for item in items for key in item if key not in BLACKLIST_FIELDS})
        header_labels = ordered_headers
        column_classes = [""] * len(ordered_headers)

    table_html = []
    if add_header:
        table_html.append(f"<h2>{escape(pretty_title)}</h2>")
    table_html.append("<table>")
    table_html.append("<tr>" + "".join(
        f"<th class='{escape(cls)}'>{escape(h)}</th>" if cls else f"<th>{escape(h)}</th>"
        for h, cls in zip(header_labels, column_classes)
    ) + "</tr>")

    emphasize_main, emphasize_add = EMPHASIZE_FIELDS.get(title.lower(), (None, None))

    for item in items:
        row = []
        for h, cls in zip(ordered_headers, column_classes):
            val = item.get(h, "")
            if isinstance(val, list) and all(isinstance(sub, dict) for sub in val):
                cell = render_subtable(val)
            elif isinstance(val, str) and contains_html(val):
                cell = val
            elif h == emphasize_main and emphasize_main in item and emphasize_add in item:
                cell = f"{escape(str(item[emphasize_main]))} <span class='emphasis'>[{escape(str(item[emphasize_add]))}]</span>"
            else:
                cell = escape(str(val))
            row.append(f"<td class='{escape(cls)}'>{cell}</td>" if cls else f"<td>{cell}</td>")
        table_html.append("<tr>" + "".join(row) + "</tr>")

    table_html.append("</table>")
    return "\n".join(table_html)

def render_value(key, value):
    pretty_title = title_for(key)

    if isinstance(value, list):
        if not value:
            return f"<h2>{escape(pretty_title)}</h2><p><em>No data</em></p>"
        elif all(isinstance(i, dict) for i in value):
            return render_table(key, value)
    elif isinstance(value, dict):
        return "\n".join(
            render_value(f"{key} - {k}", v)
            for k, v in value.items()
            if not should_skip_key(k)
        )
    elif isinstance(value, str) and contains_html(value):
        return f"<h2>{escape(pretty_title)}</h2><div>{value}</div>"
    else:
        return f"<h2>{escape(pretty_title)}</h2><pre>{escape(str(value))}</pre>"

def render_stats_table(op):
    rows = [f"<tr><th>{stat}</th><td>{escape(op.get(stat, ''))}</td></tr>" for stat in ["M", "APL", "GA", "DF", "SV", "W"]]
    rows.append(f"<tr><th>Description</th><td>{escape(op.get('description', ''))}</td></tr>")
    return "<table>" + "".join(rows) + "</table>"

def render_weapon_block(weapons):
    if not weapons:
        return ""
    html = ["<h3>Weapons</h3>", "<table><tr><th>Weapon</th><th>Type</th><th>Profiles</th></tr>"]
    for weapon in weapons:
        name = escape(weapon.get("wepname", ""))
        wtype = escape(weapon.get("weptype", ""))
        profiles = weapon.get("profiles", [])
        profile_html = render_subtable(profiles) if profiles else "<em>No profiles</em>"
        html.append(f"<tr><td>{name}</td><td>{wtype}</td><td>{profile_html}</td></tr>")
    html.append("</table>")
    return "".join(html)

def render_operatives(operatives):
    html = []
    for op in operatives:
        html.append(f"<h2>{escape(op.get('opname', 'Unnamed Operative'))}</h2>")
        html.append(render_stats_table(op))
        html.append(render_weapon_block(op.get("weapons", [])))
        if op.get("abilities"):
            html.append("<h3>Abilities</h3>")
            html.append(render_table("abilities", op["abilities"], add_header=False))
        if op.get("uniqueactions"):
            html.append("<h3>Unique Actions</h3>")
            html.append(render_table("uniqueactions", op["uniqueactions"], add_header=False))
    return "\n".join(html)

# === LOAD AND PREP DATA ===

with open("flattened_output.json", "r", encoding="utf-8") as f:
    data = json.load(f)

killteam_name = data.get("killteamname", "Unnamed Kill Team")

# === HTML HEADER ===

html_parts = [
    "<!DOCTYPE html>",
    "<html>",
    "<head>",
    "  <meta charset='UTF-8'>",
    f"  <title>{escape(killteam_name)} - Kill Team Fire Team Overview</title>",
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
    "    .emphasis { font-weight: bold; }",
    "    h2 { border-bottom: 2px solid #61dafb; padding-bottom: 0.25em; }",
    "    h3 { color: #9cdcfe; margin-top: 1.5em; }",
    "    table { margin-bottom: 1em; }",
    "	.w5   { width: 5%; }",
    "	.w10  { width: 10%; }",
    "	.w15  { width: 15%; }",
    "	.w20  { width: 20%; }",
    "	.w25  { width: 25%; }",
    "	.w30  { width: 30%; }",
    "	.w35  { width: 35%; }",
    "	.w40  { width: 40%; }",
    "	.w45  { width: 45%; }",
    "	.w50  { width: 50%; }",
    "	.w55  { width: 55%; }",
    "	.w60  { width: 60%; }",
    "	.w65  { width: 65%; }",
    "	.w70  { width: 70%; }",
    "	.w75  { width: 75%; }",
    "	.w80  { width: 80%; }",
    "	.w85  { width: 85%; }",
    "	.w90  { width: 90%; }",
    "	.w95  { width: 95%; }",
    "	.w100 { width: 100%; }",
    "  </style>",
    "</head>",
    "<body>",
    f"  <h1>{escape(killteam_name)} - Kill Team Fire Team Overview</h1>"
]

# === MAIN RENDER LOOP ===

for key in RENDER_ORDER:
    value = data.get(key)
    if not value:
        continue
    if key == "fireteams_operatives":
        html_parts.append(f"<h1>{title_for(key)}</h1>")
        html_parts.append(render_operatives(value))
    elif isinstance(value, list):
        html_parts.append(render_table(key, value))
    elif isinstance(value, dict):
        for subkey, subval in value.items():
            if isinstance(subval, list):
                html_parts.append(render_table(subkey, subval))
            else:
                html_parts.append(render_value(f"{key} - {subkey}", subval))
    else:
        if not should_skip_key(key):
            html_parts.append(render_value(key, value))

# === FINALIZE OUTPUT ===

html_parts.append("</body></html>")
Path("flattened_output_viewer.html").write_text("\n".join(html_parts), encoding="utf-8")
print("✅ HTML viewer created: flattened_output_viewer.html (clean, consistent, and ordered)")
