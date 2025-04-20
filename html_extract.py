from bs4 import BeautifulSoup, Tag, Comment, NavigableString
import re

# --- TEXT CLEANUP FUNCTION --------------------------------------------------

def clean_text(text):
    """
    Clean and normalize text by:
    - Splitting on multiple newlines to create paragraphs
    - Normalizing whitespace within each paragraph
    - Wrapping each paragraph in a <p> tag
    """
    if not text:
        return ''

    # Split text into paragraphs based on 2+ newlines
    paragraphs = re.split(r'\n{2,}', text)

    cleaned_paragraphs = []
    for para in paragraphs:
        cleaned = re.sub(r'\s+', ' ', para).strip()
        if cleaned:
            cleaned_paragraphs.append(f'<p>{cleaned}</p>')

    return ''.join(cleaned_paragraphs)



# --- HTML TO CLEAN DIV STRUCTURE -------------------------------------------

def clean_to_div_tree(element, soup):
    """
    Recursively convert an HTML element into a cleaned structure that:
    - Preserves original tag types (h2, li, ul, etc.)
    - Removes all attributes (class, id, etc.)
    - Converts raw text into <p> tags for paragraphs
    - Recursively processes children
    """

    # Create a new tag using the same name as the original (e.g., 'h2', 'ul', 'li')
    clean_tag = soup.new_tag(element.name)

    # Go through each child node of this element
    for child in element.children:

        # If it's a raw text node (NavigableString), clean and wrap it in <p>
        if isinstance(child, str):
            cleaned = clean_text(child)
            if cleaned:
                # Parse the cleaned string so HTML tags like <p> are kept as real tags
                parsed = BeautifulSoup(cleaned, 'html.parser')
                clean_tag.append(parsed)

        # If it's an HTML tag (e.g., <a>, <span>, <div>, etc.), process recursively
        elif isinstance(child, Tag):
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
