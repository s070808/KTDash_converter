from bs4 import BeautifulSoup, Tag, Comment, NavigableString
import re

# Tags that should be excluded from export even if class matches
blocked_tags = ['button','input','textarea']

# --- TEXT CLEANUP FUNCTION --------------------------------------------------

def clean_text(text):
    """
    Clean and normalize text by:
    - Removing leading/trailing whitespace
    - Replacing any sequence of whitespace (tabs, newlines, multiple spaces) with a single space
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
    - Recursively processes children and builds the cleaned output
    """

    # Create a new tag using the same name as the original (e.g., 'div', 'h2', etc.)
    clean_tag = soup.new_tag(element.name)

    # Determine whether this is a heading tag (h1–h6)
    is_heading = element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']

    for child in element.children:

        # Case 1: Raw text
        if isinstance(child, str):
            cleaned = clean_text(child)
            if cleaned:
                if is_heading:
                    clean_tag.append(cleaned)
                else:
                    # Wrap cleaned text in a real <p> tag
                    p_tag = soup.new_tag("p")
                    p_tag.string = cleaned
                    clean_tag.append(p_tag)

        # Case 2: Nested tag
        elif isinstance(child, Tag):
            if child.name in blocked_tags:
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
            # Skip blocked tags (e.g., <button>, <script>, etc.)
            if el.name in blocked_tags:
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
    class_names = ['pointer', 'tab-pane', 'modal-content']  # Add or replace with your own

    # Run the extraction
    extract_clean_divs(input_path, class_names, output_path)
