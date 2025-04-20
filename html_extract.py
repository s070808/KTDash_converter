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
    each containing clean, readable text with <p> tags for paragraph separation.

    - Converts all HTML tag types to <div> for consistency
    - Ignores empty text nodes and comment tags
    - Uses <p> tags to preserve paragraphs based on newline separation
    - Parses cleaned text as HTML to prevent escaping (<p> rendered properly)
    - Recursively builds a div-only hierarchy
    """
    div = soup.new_tag("div")  # Create a new <div> wrapper for this element's content

    # Case 1: Element contains only direct text (no child tags)
    if element.string and element.string.strip():
        # Clean the string and parse as HTML so <p> tags are interpreted correctly
        parsed_html = BeautifulSoup(clean_text(element.string), 'html.parser')
        div.append(parsed_html)  # Append parsed <p> tag(s) directly into the <div>

    else:
        # Case 2: Element contains children (tags or nested text nodes)
        for child in element.children:

            # If the child is a plain text node (not a tag)
            if isinstance(child, str):
                if child.strip():  # Skip empty or whitespace-only nodes
                    text_div = soup.new_tag("div")  # Wrap this text block in its own <div>
                    # Clean the text and parse HTML tags like <p> within it
                    parsed_text = BeautifulSoup(clean_text(child), 'html.parser')
                    text_div.append(parsed_text)  # Append parsed <p> tags into text <div>
                    div.append(text_div)  # Add text block to parent <div>

            # If the child is an HTML tag (e.g., <span>, <div>, etc.)
            elif isinstance(child, Tag):
                # Recursively convert child tag to a clean <div> tree
                div.append(clean_to_div_tree(child, soup))

    return div  # Return the fully constructed <div> for this node


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
