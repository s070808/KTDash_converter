from bs4 import BeautifulSoup, Tag, Comment, NavigableString
import re

# Tags that should be excluded from export even if class matches
blocked_tags = ['button','input','textarea']

# --- IGNORE COMMENTS AND WHITESPACE LINES  --------------------------------------------------

def is_comment_only(el):
    """
    Returns True if all contents of the element (and its descendants)
    are either comments or whitespace (no visible text).
    """
    for desc in el.descendants:
        if isinstance(desc, Comment):
            continue
        if isinstance(desc, NavigableString) and desc.strip():
            return False  # Found real text
        if isinstance(desc, Tag):
            if not is_comment_only(desc):
                return False
    return True



# --- ANGULAR FUNCTIONS REMOVAL  --------------------------------------------------

def contains_angular_syntax(el):
    """
    Returns True if the element has text or attributes that start with 'ng'
    (e.g., ngRepeat, ngIf), used to filter out Angular-generated lines.
    """
    # Check all attributes (both names and values)
    for attr, val in el.attrs.items():
        if attr.startswith("ng"):
            return True
        if isinstance(val, list):
            if any(str(v).startswith("ng") for v in val):
                return True
        elif isinstance(val, str) and val.startswith("ng"):
            return True

    # Check direct and descendant text content
    for text in el.strings:
        if isinstance(text, NavigableString) and 'ng' in text and re.search(r'\bng\w+', text):
            return True

    return False


# --- TEXT CLEANUP FUNCTION --------------------------------------------------

def clean_text(text):
    """
    Normalize whitespace in text:
    - Replace tabs, newlines, and repeated spaces with a single space
    - Strip leading/trailing space
    """
    if not text:
        return ''
    return re.sub(r'\s+', ' ', text).strip()





# --- HTML TO CLEAN DIV STRUCTURE -------------------------------------------

def clean_to_div_tree(element, soup):
    """
    Recursively convert an HTML element into a cleaned structure that:
    - Preserves original tag types (h2, li, ul, etc.)
    - Removes all attributes (class, id, etc.)
    - Converts raw text into <p> tags for paragraphs (unless inside <h1>-<h6>)
    - Skips any tags listed in `blocked_tags`
    - Skips all HTML comments (even visible ones)
    - Recursively processes children and builds the cleaned output
    """

    clean_tag = soup.new_tag(element.name)
    is_heading = element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']

    for child in element.children:

        # ❌ Skip all comment blocks — anything wrapped in <!-- ... -->
        if isinstance(child, Comment):
            continue

        # ✅ Handle text nodes
        if isinstance(child, str):
            cleaned = clean_text(child)
            if cleaned:
                if is_heading:
                    clean_tag.append(cleaned)
                else:
                    p_tag = soup.new_tag("p")
                    p_tag.string = cleaned
                    clean_tag.append(p_tag)

        # ✅ Handle nested tags
        elif isinstance(child, Tag):
            if child.name in blocked_tags:
                continue
            if is_comment_only(child):
                continue
            if contains_angular_syntax(child):
                continue
            cleaned_child = clean_to_div_tree(child, soup)
            clean_tag.append(cleaned_child)

    return clean_tag








# --- MAIN FUNCTION TO PROCESS HTML FILE -------------------------------------

def extract_clean_divs(input_html_path, class_names, output_html_path):
    """
    Load an HTML file, extract elements matching the given class names,
    convert their contents into <div>-only structure with cleaned text, and
    output a new, styled HTML file containing just the cleaned content.
    """
    # Read and parse the input HTML file
    with open(input_html_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')

    # Build a fresh new HTML structure with basic dark styling
    new_soup = BeautifulSoup('''<html><head><title>Extracted Divs</title><style>body {background-color: #1e1e1e;color: #f0f0f0;font-family: sans-serif;padding: 20px;}div {margin-bottom: 1em;}</style></head><body></body></html>''', 'html.parser')

    new_body = new_soup.body  # Reference to new <body> tag

    # For each class name to look for in the original HTML...
    for class_name in class_names:
        # Collect all elements that match any class name, maintaining document order
        elements = [
            el for el in soup.find_all(True)
            if el.has_attr("class") and any(cls in class_names for cls in el["class"])
        ]

        for el in elements:
            # Skip blocked tags
            if el.name in blocked_tags:
                continue
            # Skip if comment-only block
            if is_comment_only(el):
                continue

            # Skip if Angular directives or 'ngSomething' is detected
            if contains_angular_syntax(el):
                continue

            # Skip if there's no visible text
            has_visible_text = any(
                isinstance(child, NavigableString) and not isinstance(child, Comment) and child.strip()
                for child in el.descendants
            )
            if not has_visible_text:
                continue

            clean_div = clean_to_div_tree(el, new_soup)
            if clean_div:
                new_body.append(clean_div)

    # Write the final cleaned HTML output to file
    with open(output_html_path, 'w', encoding='utf-8') as file:
        file.write(new_soup.prettify())

# --- RUN SCRIPT (EXAMPLE USAGE) --------------------------------------------

if __name__ == '__main__':
    # Path to the local HTML file you want to process
    input_path = 'C:/Stuff/GIT/KTDash_converter/input.html'

    # Path where the cleaned output HTML will be saved
    output_path = 'C:/Stuff/GIT/KTDash_converter/extracted_output.html'

    # Class names to extract from the HTML (only these will be processed)
    class_names = ['tab-content', 'p-1']  # Add or replace with your own

    # Run the extraction
    extract_clean_divs(input_path, class_names, output_path)
