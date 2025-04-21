import json
from pathlib import Path
from html import escape
import html
import re

# === CONFIGURATION ===
team_name = "ktdash_gk"
input_path_html = f"html/{team_name}.html"
input_temp_json = "pretty_output.json"
intermediate_json = "cleaned_output.json"

input_flattened_json = "flattened_output.json"
output_file_html = "html/"

# Keys to remove from top level
input_keys_to_ignore = ["rosters"]

# Nested keys to flatten recursively
input_flatten_targets = {
    "operatives": ["abilities", "weapons", "uniqueactions"],
    "fireteams": ["operatives"]
}

BLACKLIST_KEYS = {"fireteams", "operatives_weapons", "customkeyword", "killteamname"}
BLACKLIST_FIELDS = {
    "factionid", "killteamid", "ployid", "ploytype", "eqcategory", "eqid", "eqvar1", "eqvar2", "eqvar3", "eqvar4",
    "fireteamid", "opid", "eqpts", "eqseq", "edition", "tacopid", "tacopseq", "abilityid", "isdefault",
    "isselected", "wepid", "wepseq", "eqtype", "weapon", "name", "profileid"
}

HORIZONTAL_TABLES = {
    "fireteams_operatives": [
        ("M", "Move"),
        ("APL", "APL"),
        ("SV", "Save"),
        ("W", "Wounds")
    ]
}

H1_HEADERS = {
    "ploys": "Ploys",
    "equipments": "Equipment List",
    "tacops": "Tactical Objectives",
    # Add more if needed
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
        ("eqname", "Name", "w20"),         # Can be slightly longer
        ("eqdescription", "Description", "w80")
    ],
    "tacops": [
        ("title", "Title", "w20"),         # Brief, but longer than a name
        ("description", "Description", "w80")
    ],
    "operatives_abilities": [              # Faction Rules
        ("title", "Title", "w10"),         # Often a short phrase
        ("description", "Description", "w90")
    ],
    "weapons": [
        ("wepname", "Weapon", "w15"),      # Longer names like "Shuriken Catapult"
        ("weptype", "Ranged/Melee", "w10"),# Short tag
        ("profiles", "Profiles", "w75")    # Table goes here, needs width
    ],
    "abilities": [
        ("title", "Title", "w10"),
        ("description", "Description", "w90")
    ],
    "weapons": [
        ("wepname", "Weapon", "w10"),
        ("weptype", "Ranged/Melee", "w5"),
        ("profiles", "Profiles", "w85")
    ],
    "profiles": [
        ("A", "Atk", "w10"),
        ("BS", "Hit", "w10"),
        ("D", "Dmg", "w10"),
        ("SR", "Wr", "w70")
    ],
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

# === HTML STUFF

def convert_broken_json_from_file():
    # Step 1: Read the entire HTML file
    try:
        html_content = Path(input_path_html).read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"❌ File '{input_path_html}' not found.")
        return

    # Step 2: Extract the killteam="..." attribute from <body ...>
    match = re.search(r'killteam="([^"]+)"', html_content)
    if not match:
        print("❌ No killteam attribute found in HTML.")
        return

    html_encoded_json = match.group(1)

    # Step 3: Unescape HTML entities
    decoded_json_str = html.unescape(html_encoded_json)

    # Step 4: Parse JSON
    try:
        data = json.loads(decoded_json_str)
    except json.JSONDecodeError as e:
        print("❌ JSON parsing failed:")
        print(e)
        return

    # Step 5: Pretty-print JSON to file
    pretty_json = json.dumps(data, indent=4)
    Path(input_temp_json).write_text(pretty_json, encoding="utf-8")
    print(f"✔️ Pretty JSON written to '{input_temp_json}'.")

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


def clean_and_flatten():
    # === Load broken JSON from https://ktdash.app/ into json file
    convert_broken_json_from_file()

    # === Load original JSON ===
    with open(input_temp_json, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    # === Step 1: Remove unwanted keys ===
    cleaned_data = remove_keys(json_data, input_keys_to_ignore)
    with open(intermediate_json, "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, indent=4)
    print(f"🧹 Cleaned JSON written to {intermediate_json} (without: {', '.join(input_keys_to_ignore)})")

    # === Step 2: Flatten deeply nested shared children ===
    flattened_data = flatten_all(cleaned_data, input_flatten_targets)
    with open(input_flattened_json, "w", encoding="utf-8") as f:
        json.dump(flattened_data, f, indent=4)
    print(f"📦 Deep-flattened JSON written to {input_flattened_json}")

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

def render_keywords(keywords):
    if not keywords:
        return ""

    tags = [kw.strip() for kw in keywords.split(",") if kw.strip()]
    html_tags = " ".join(f"<span class='keyword-tag'>{escape(tag)}</span>" for tag in tags)
    return f"<div class='keywords-block'><strong>Keywords:</strong> {html_tags}</div>"


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

def render_stats_table(op, source_key="fireteams_operatives"):
    fields = HORIZONTAL_TABLES.get(source_key)
    if not fields:
        return ""

    headers = "".join(f"<th>{escape(label)}</th>" for _, label in fields)
    values = "".join(f"<td>{escape(op.get(field, ''))}</td>" for field, _ in fields)

    return f"<table><tr>{headers}</tr><tr>{values}</tr></table>"

def render_weapon_block(weapons):
    if not weapons:
        return ""

    html = ["<h3>Weapons</h3>", "<table>"]

    # Pull column config
    column_config = COLUMN_CONFIG.get("weapons", [])
    headers = [label for _, label, *_ in column_config]
    fields = [field for field, *_ in column_config]
    classes = [col[2] if len(col) > 2 else "" for col in column_config]

    # Render header row
    html.append("<tr>" + "".join(
        f"<th class='{escape(cls)}'>{escape(label)}</th>" if cls else f"<th>{escape(label)}</th>"
        for label, cls in zip(headers, classes)
    ) + "</tr>")

    # Render data rows
    for weapon in weapons:
        row = []
        for field, cls in zip(fields, classes):
            val = weapon.get(field, "")
            if field == "profiles":
                content = render_profiles_table(val)
            elif isinstance(val, list) and all(isinstance(sub, dict) for sub in val):
                content = render_subtable(val)
            else:
                content = escape(str(val)) if not contains_html(str(val)) else val
            row.append(f"<td class='{escape(cls)}'>{content}</td>" if cls else f"<td>{content}</td>")
        html.append("<tr>" + "".join(row) + "</tr>")

    html.append("</table>")
    return "".join(html)

def render_profiles_table(profiles):
    column_config = COLUMN_CONFIG.get("profiles", [])
    if not profiles or not column_config:
        return "<em>No profiles</em>"

    headers = [label for _, label, *_ in column_config]
    fields = [field for field, *_ in column_config]
    classes = [col[2] if len(col) > 2 else "" for col in column_config]

    html = ["<table>"]
    html.append("<tr>" + "".join(
        f"<th class='{escape(cls)}'>{escape(label)}</th>" if cls else f"<th>{escape(label)}</th>"
        for label, cls in zip(headers, classes)
    ) + "</tr>")

    for profile in profiles:
        row = []
        for field, cls in zip(fields, classes):
            val = profile.get(field, "")
            cell = escape(str(val)) if not contains_html(str(val)) else val
            row.append(f"<td class='{escape(cls)}'>{cell}</td>" if cls else f"<td>{cell}</td>")
        html.append("<tr>" + "".join(row) + "</tr>")

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

        if op.get("keywords"):
            html.append(render_keywords(op["keywords"]))

        if op.get("uniqueactions"):
            html.append("<h3>Unique Actions</h3>")
            html.append(render_table("uniqueactions", op["uniqueactions"], add_header=False))
    return "\n".join(html)

# === LOAD AND PREP DATA ===

# Handle load of ktdash file
clean_and_flatten()

# Handle html-ification of JSON
with open(input_flattened_json, "r", encoding="utf-8") as f:
    data = json.load(f)

killteam_name = data.get("killteamname", "Unnamed Kill Team")
current_killteam_id = data.get("killteamid", "").upper()

# === HTML HEADER ===

html_parts = [
    "<!DOCTYPE html>",
    "<html>",
    "<head>",
    "  <meta charset='UTF-8'>",
    f"  <title>{escape(killteam_name)} - Kill Team Overview (Homebrew)</title>",
    "  <style>",
    "    body { background: #1e1e1e; color: #d4d4d4; font-family: 'Segoe UI', sans-serif; padding: 2em; }",
    "    h1, h2 { color: #D55F23; }",
    "    table { border-collapse: collapse; width: 100%; margin-bottom: 2em; }",
    "    th, td { border: 1px solid #333; padding: 8px; text-align: left; vertical-align: top; }",
    "    th { background-color: #333; color: #ffffff; }",
    "    tr:nth-child(even) { background-color: #2a2a2a; }",
    "    tr:nth-child(odd) { background-color: #252526; }",
    "    pre { background: #2d2d2d; padding: 1em; border-radius: 6px; overflow-x: auto; white-space: pre-wrap; }",
    "    a { color: #D55F23; }",
    "    .emphasis { font-weight: bold; }",
    "    h2 { border-bottom: 2px solid #D55F23; padding-bottom: 0.25em; }",
    "    h3 { color: #D55F23; margin-top: 1.5em; }",
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
    "	.keywords-block {",
    "	  margin-top: 1em;",
    "	  font-size: 0.95em;",
    "	  color: #cccccc;",
    "	}",
    "	",
    "	.keyword-tag {",
    "	  display: inline-block;",
    "	  background-color: #333;",
    "	  color: #D55F23;",
    "	  border-radius: 12px;",
    "	  padding: 0.2em 0.6em;",
    "	  margin: 0.1em;",
    "	  font-weight: 500;",
    "	  font-size: 0.9em;",
    "	  white-space: nowrap;",
    "	}",
    "	footer.credits {",
    "	  border-top: 1px solid #444;",
    "	  margin-top: 3em;",
    "	  padding-top: 1.5em;",
    "	  font-size: 0.9em;",
    "	  color: #aaaaaa;",
    "	}",
    "	",
    "	",
    "	footer.credits a:hover {",
    "	  text-decoration: underline;",
    "	}",
    "  </style>",
    "</head>",
    "<body>",
    f"  <h1>{escape(killteam_name)} - Kill Team Overview (Homebrew)</h1>"
]

# === MAIN RENDER LOOP ===

for key in RENDER_ORDER:
    value = data.get(key)
    if not value:
        continue

    # Insert a custom <h1> header if this key has one
    if key in H1_HEADERS:
        html_parts.append(f"<h1>{escape(H1_HEADERS[key])}</h1>")

    if key == "fireteams_operatives":
        html_parts.append(render_operatives(value))

    elif key == "equipments" and isinstance(value, list):
        # Dynamically split equipment by killteamid
        team_equip = [e for e in value if e.get("killteamid", "").upper() == current_killteam_id]
        universal_equip = [e for e in value if e.get("killteamid", "").upper() == "ALL"]

        if team_equip:
            html_parts.append(f"<h2>{killteam_name} Equipment</h2>")
            html_parts.append(render_table("equipments", team_equip, add_header=False))  # ✅ Suppress auto <h2>

        if universal_equip:
            html_parts.append("<h2>Universal Equipment</h2>")
            html_parts.append(render_table("equipments", universal_equip, add_header=False))  # ✅ Suppress auto <h2>


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
output_file_html = output_file_html + current_killteam_id + ".html"

html_parts.append("""
  <footer class="credits">
    <h2>Credits</h2>
    <p>This document is based on data from <a href="https://ktdash.app/fa/HBR/kt/GK24" target="_blank">KT Dash – Grey Knights Kill Team</a>.</p> 
    <p>Recompiled and structured by <a href="https://cults3d.com/en/users/s070808/3d-models" target="_blank">s070808 @ Cults3d</a></p>
  </footer>
""")
html_parts.append("</body></html>")
Path(output_file_html).write_text("\n".join(html_parts), encoding="utf-8")
print("✅ HTML viewer created: {output_file}} (clean, consistent, and ordered)")
