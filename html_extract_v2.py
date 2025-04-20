from bs4 import BeautifulSoup, Tag, Comment, NavigableString


# Tags that should be excluded from export even if class matches
blocked_tags = ['button', 'input', 'textarea']

def clean_to_div_tree(element, soup):
    """Recursively copy only tag structure and visible text — strip all attributes, skip blocked tags."""
    if not isinstance(element, Tag):
        return None

    # Skip the entire tag and its subtree if it's in the blocked list
    if element.name in blocked_tags:
        return None

    # Create the tag (without any attributes)
    clean_tag = soup.new_tag(element.name)

    for child in element.children:
        if isinstance(child, Comment):
            continue
        elif isinstance(child, Tag):
            nested = clean_to_div_tree(child, soup)
            if nested:
                clean_tag.append(nested)
        elif isinstance(child, NavigableString):
            text = child.strip()
            if text:
                clean_tag.append(text)

    return clean_tag if clean_tag.contents else None




def parse_input_html(input_html_path):
    """Load the HTML file and return the BeautifulSoup object of its <body>."""
    with open(input_html_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
    
    return soup.body if soup.body else soup  # fallback to full soup if no <body>


def create_output_soup():
    """Create a new HTML soup with custom head and empty body."""
    html_str = '''<html><head><title>Extracted Divs</title><style>
        body {background-color: #1e1e1e; color: #f0f0f0; font-family: sans-serif; padding: 20px;}
        div {margin-bottom: 1em;}
    </style></head><body></body></html>'''
    
    return BeautifulSoup(html_str, 'html.parser')


def process_and_clean_content(input_body, output_soup):
    """Copy cleaned, visible content from input body to output soup."""
    new_body = output_soup.body

    for el in input_body.find_all(True, recursive=True):
        has_visible_text = any(
            isinstance(child, NavigableString) and not isinstance(child, Comment) and child.strip()
            for child in el.descendants
        )
        if not has_visible_text:
            continue

        clean_el = clean_to_div_tree(el, output_soup)
        if clean_el:
            new_body.append(clean_el)

    return output_soup


def save_output_html(output_soup, output_html_path):
    """Save the final cleaned soup to an output file."""
    with open(output_html_path, 'w', encoding='utf-8') as file:
        file.write(output_soup.prettify())


def extract_clean_divs(input_html_path, output_html_path):
    """High-level function to run the full extract-transform-save pipeline."""
    input_body = parse_input_html(input_html_path)
    output_soup = create_output_soup()
    cleaned_soup = process_and_clean_content(input_body, output_soup)
    save_output_html(cleaned_soup, output_html_path)



if __name__ == '__main__':
    # Path to the local HTML file you want to process
    input_path = 'C:/Stuff/GIT/KTDash_converter/input.html'

    # Path where the cleaned output HTML will be saved
    output_path = 'C:/Stuff/GIT/KTDash_converter/extracted_output.html'

    # Run the extraction
    extract_clean_divs(input_path, output_path)