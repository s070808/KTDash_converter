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

    # Split into blocks by 2+ newlines to identify paragraphs
    paragraphs = re.split(r'\n{2,}', text)

    cleaned_paragraphs = []
    for para in paragraphs:
        # Replace all internal whitespace (spaces, tabs, newlines) with single space
        cleaned = re.sub(r'\s+', ' ', para).strip()
        if cleaned:
            cleaned_paragraphs.append(f'<p>{cleaned}</p>')

    return ''.join(cleaned_paragraphs)


# --- HTML TO CLEAN DIV STRUCTURE -------------------------------------------

def clean_to_div_tree(element, soup):
    """
    Recursively convert an HTML element and its children into a structure made only of <div> tags,
    each containing clean, readable text.

    - Ignores HTML tag types (all become <div>)
    - Skips empty text nodes and comment tags
    - Recursively traverses child tags and builds div-based hierarchy
    """
    div = soup.new_tag("div")  # Create a new <div> tag to hold cleaned content

    # If this element only contains a direct text node (not other tags)
    if element.string and element.string.strip():
        div.string = clean_text(element.string)  # Clean and assign the text directly
    else:
        # Otherwise loop through all children of this tag
        for child in element.children:
            # If child is a plain text node (not a tag)
            if isinstance(child, str):
                if child.strip():  # Ignore pure whitespace nodes
                    text_div = soup.new_tag("div")  # Wrap text in a new <div>
                    text_div.string = clean_text(child)  # Clean and add the text
                    div.append(text_div)
            # If child is a tag (e.g., <span>, <p>, <div>...), process it recursively
            elif isinstance(child, Tag):
                div.append(clean_to_div_tree(child, soup))

    return div  # Return the full cleaned <div> tree

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
        # Find all elements in the input HTML with that class
        elements = soup.find_all(class_=class_name)

        for el in elements:
            # Only process if the element or its children contain visible (non-comment, non-whitespace) text
            has_visible_text = any(
                isinstance(child, NavigableString) and not isinstance(child, Comment) and child.strip()
                for child in el.descendants
            )
            if not has_visible_text:
                continue  # Skip completely empty or comment-only blocks

            # Convert this element into a clean <div> tree
            clean_div = clean_to_div_tree(el, new_soup)
            if clean_div:
                new_body.append(clean_div)  # Add to the new <body>

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
    class_names = ['pointer', 'tab-pane']  # Add or replace with your own

    # Run the extraction
    extract_clean_divs(input_path, class_names, output_path)
