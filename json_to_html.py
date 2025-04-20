import json
from pathlib import Path
from html import escape
import re

# Keys to ignore at the top level
BLACKLIST_KEYS = {"fireteams", "operatives_weapons", "customkeyword","killteamname"}  # top-level
BLACKLIST_FIELDS = {
    "factionid", "killteamid", "ployid", "ploytype", "eqcategory", "eqid",
    "eqvar1", "eqvar2", "eqvar3", "eqvar4", "fireteamid", "opid", "eqpts",
    "eqseq", "edition", "tacopid", "tacopseq", "abilityid", "isdefault",
    "isselected", "wepid", "wepseq", "eqtype", "weapon", "eqtype",
    "factionid","fireteamid","killteamid","name","opid","profileid","wepid"
}
COLUMN_CONFIG = {
    "strat": [("ployname", "Name"), ("CP", "CP"), ("description", "Description")],
    "tac": [("ployname", "Name"), ("CP", "CP"), ("description", "Description")],
    "equipments": [("eqname", "Name"), ("eqdescription", "Description")],
    "tacops": [("title", "Title"), ("description", "Description")],
    "operatives_abilities": [("title", "Title"), ("description", "Description")],
    "weapons": [("wepname", "Weapon"), ("weptype", "Ranged/Melee"), ("profiles", "Profiles")],
    "abilities": [("title", "Title"), ("description", "Description")],

}

# Custom display rules per parent key
EMPHASIZE_FIELDS = {
    "equipments": ("eqname", "eqtype"),  # Show eqname [eqtype]
    "tacops": ("title", "archetype"),  # Show eqname [eqtype]
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
}

# Keys that are handled manually in a parent (e.g., inside render_operatives)
SKIP_RENDER_KEYS = {"weapons", "abilities", "uniqueactions"}


# Load the flattened JSON
with open("flattened_output.json", "r", encoding="utf-8") as f:
    data = json.load(f)

killteam_name = data.get("killteamname", "Unnamed Kill Team")





# Start HTML
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
    "    .emphasis { font-weight: bold;  }",
    "   h2 { border-bottom: 2px solid #61dafb; padding-bottom: 0.25em; }",
    "   h3 { color: #9cdcfe; margin-top: 1.5em; }",
    "   table { margin-bottom: 1em; }",
    "  </style>",
    "</head>",
    "<body>",
    f"  <h1>{escape(killteam_name)} - Kill Team Fire Team Overview</h1>"
]


### function definitions


def render_operatives(operatives):
    html = []
    for op in operatives:
        html.append(f"<h2>{escape(op.get('opname', 'Unnamed Operative'))}</h2>")
        html.append("<table>")
        for stat in ["M", "APL", "GA", "DF", "SV", "W"]:
            html.append(f"<tr><th>{stat}</th><td>{escape(op.get(stat, ''))}</td></tr>")
        html.append(f"<tr><th>Description</th><td>{escape(op.get('description', ''))}</td></tr>")
        html.append("</table>")

        # Weapons
        if op.get("weapons"):
            html.append("<h3>Weapons</h3>")
            weapon_rows = []
            for weapon in op["weapons"]:
                wepname = escape(weapon.get("wepname", ""))
                weptype = escape(weapon.get("weptype", ""))
                profiles = weapon.get("profiles", [])

                if profiles and all(isinstance(p, dict) for p in profiles):
                    # Filter out blacklisted fields
                    headers = sorted({k for p in profiles for k in p if k not in BLACKLIST_FIELDS})
                    profile_table = ["<table>"]
                    profile_table.append("<tr>" + "".join(f"<th>{escape(h)}</th>" for h in headers) + "</tr>")
                    for p in profiles:
                        profile_table.append("<tr>" + "".join(f"<td>{escape(str(p.get(h, '')))}</td>" for h in headers) + "</tr>")
                    profile_table.append("</table>")
                    profile_html = "".join(profile_table)
                else:
                    profile_html = "<em>No profiles</em>"

                weapon_rows.append(f"<tr><td>{wepname}</td><td>{weptype}</td><td>{profile_html}</td></tr>")

            html.append("<table>")
            html.append("<tr><th>Weapon</th><th>Type</th><th>Profiles</th></tr>")
            html.extend(weapon_rows)
            html.append("</table>")



        # Abilities
        if op.get("abilities"):
            html.append("<h3>Abilities</h3>")
            html.append(render_table("Abilities", op["abilities"], add_header=False))

        # Unique Actions
        if op.get("uniqueactions"):
            html.append("<h3>Unique Actions</h3>")
            html.append(render_table("Unique Actions", op["uniqueactions"], add_header=False))

    return "\n".join(html)

def contains_html(s):
    return bool(re.search(r"</?[a-z][\s\S]*?>", s, re.IGNORECASE))

def render_table(title, items, add_header=True):
    if not items:        
        return f"<h2>{TITLE_OVERRIDES.get(title.lower(), title)}</h2><p><em>No data</em></p>"

    # Column ordering and pretty header names
    if title.lower() in COLUMN_CONFIG:
        ordered_headers = [field for field, _ in COLUMN_CONFIG[title.lower()]]
        header_labels = [label for _, label in COLUMN_CONFIG[title.lower()]]
    else:
        ordered_headers = sorted({key for item in items for key in item if key not in BLACKLIST_FIELDS})
        header_labels = ordered_headers

    pretty_title = TITLE_OVERRIDES.get(title.lower(), title)
    table_html = []
    if add_header:
        table_html.append(f"<h2>{escape(pretty_title)}</h2>")
    table_html.append("<table>")
    table_html.append("<tr>" + "".join(f"<th>{escape(h)}</th>" for h in header_labels) + "</tr>")

    # Custom emphasis rule for specific tables
    emphasize_main, emphasize_add = EMPHASIZE_FIELDS.get(title.lower(), (None, None))

    for item in items:
        row = []
        for h in ordered_headers:
            val = item.get(h, "")
            if isinstance(val, list) and all(isinstance(sub, dict) for sub in val):
                # Render inner table for list of dicts
                inner_table = ["<table>"]
                inner_headers = sorted({k for d in val for k in d if k not in BLACKLIST_FIELDS})
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
                # Apply emphasized display if applicable
                if h == emphasize_main and emphasize_main in item and emphasize_add in item:
                    main_val = escape(str(item[emphasize_main]))
                    add_val = escape(str(item[emphasize_add]))
                    combined = f'{main_val} <span class="emphasis">[{add_val}]</span>'
                    row.append(f"<td>{combined}</td>")
                else:
                    row.append(f"<td>{escape(str(val))}</td>")
        table_html.append("<tr>" + "".join(row) + "</tr>")

    table_html.append("</table>")
    return "\n".join(table_html)


# Recursively render any dict/list combo
def render_value(key, value):
    if isinstance(value, list):
        if not value:
            return f"<h2>{TITLE_OVERRIDES.get(key.lower(), key)}</h2><p><em>No data</em></p>"
        elif all(isinstance(i, dict) for i in value):
            return render_table(key, value)
    elif isinstance(value, dict):
        return "\n".join(
            render_value(f"{key} - {k}", v)
            for k, v in value.items()
            if k not in BLACKLIST_FIELDS
        )
    elif isinstance(value, str) and contains_html(value):
        return f"<h2>{TITLE_OVERRIDES.get(key.lower(), key)}</h2><div>{value}</div>"  # render embedded HTML
    else:
        return f"<h2>{TITLE_OVERRIDES.get(key.lower(), key)}</h2><pre>{escape(str(value))}</pre>"

# Render all top-level keys
for key, value in data.items():
    if key in BLACKLIST_KEYS:
        continue  # Skip keys in the blacklist

    if isinstance(value, list):
        if key == "fireteams_operatives":
            html_parts.append(f"<h1>{TITLE_OVERRIDES.get(key.lower(), key)}</h1>")
            html_parts.append(render_operatives(value))
        else:
            html_parts.append(render_table(key, value))
    elif isinstance(value, dict):
        for subkey, subval in value.items():
            if isinstance(subval, list):
                # Preserve subkey for COLUMN_CONFIG lookup
                html_parts.append(render_table(subkey, subval))
            else:
                html_parts.append(render_value(f"{key} - {subkey}", subval))

    else:
        # NEW: render simple fields (str, int, etc.) that aren't in lists or dicts
        if key not in BLACKLIST_FIELDS:
            html_parts.append(render_value(key, value))


# Finalize
html_parts.append("</body></html>")
Path("flattened_output_viewer.html").write_text("\n".join(html_parts), encoding="utf-8")
print("✅ HTML viewer created: flattened_output_viewer.html (with proper nested support and emphasis)")
