from bs4 import BeautifulSoup, Tag, Comment, NavigableString
import hashlib


# Tags that should be excluded from export even if class matches
blocked_tags = ['button', 'input', 'textarea']

remove_all_before_this_tag_class_first_appear = ['h1','orange']
remove_all_after_class_first_appear = ''

def remove_all_before_tag(soup, tag_name, class_name):
    """
    Removes all content in <body> before the first occurrence of the given tag with the specified class.
    """
    body = soup.body
    if not body:
        return soup

    removing = True
    new_body_contents = []

    for element in body.contents:
        if removing:
            # Check this element or any of its descendants
            if (
                isinstance(element, Tag) and
                (
                    (element.name == tag_name and class_name in element.get("class", [])) or
                    element.find(tag_name, class_=class_name)
                )
            ):
                removing = False
                new_body_contents.append(element)
        else:
            new_body_contents.append(element)

    body.clear()
    for el in new_body_contents:
        body.append(el)

    return soup

def unwrap_redundant_div_layers(soup):
    """
    Recursively unwraps <div> layers that only contain one <div> with multiple children,
    effectively flattening unnecessary wrapper divs.
    """
    def is_single_child_div(tag):
        return (
            tag.name == "div" and
            len([c for c in tag.contents if isinstance(c, Tag) or str(c).strip()]) == 1 and
            isinstance(tag.contents[0], Tag) and
            tag.contents[0].name == "div"
        )

    changed = True
    while changed:
        changed = False
        for div in soup.find_all("div"):
            if is_single_child_div(div):
                inner_div = div.contents[0]
                div.replace_with(inner_div)
                changed = True
                break  # Restart to avoid iterator invalidation

    return soup

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

def remove_duplicate_blocks(cleaned_soup):
    """Deduplicate repeated tag structures (e.g., repeated <div> trees) from the soup."""
    new_soup = BeautifulSoup(str(cleaned_soup), 'html.parser')
    body = new_soup.body

    seen_hashes = set()
    unique_content = []

    for tag in body.find_all(recursive=False):  # Only look at top-level children of <body>
        tag_hash = hashlib.md5(tag.encode_contents()).hexdigest()
        if tag_hash not in seen_hashes:
            print("Duplicate block removed:")
            print(tag.prettify())
            seen_hashes.add(tag_hash)
            unique_content.append(tag)

    # Clear and re-append unique blocks
    body.clear()
    for tag in unique_content:
        body.append(tag)

    return new_soup


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
        table {width: 100%;}
    </style></head><body></body></html>'''
    
    return BeautifulSoup(html_str, 'html.parser')


def process_and_clean_content(input_body, output_soup):
    """Copy cleaned, visible, non-duplicate content from input body to output soup."""
    new_body = output_soup.body
    seen_hashes = set()

    for el in input_body.find_all(True, recursive=True):
        has_visible_text = any(
            isinstance(child, NavigableString) and not isinstance(child, Comment) and child.strip()
            for child in el.descendants
        )
        if not has_visible_text:
            continue

        clean_el = clean_to_div_tree(el, output_soup)
        if clean_el:
            # Serialize to string to check for duplicates
            content_hash = hashlib.md5(clean_el.encode_contents()).hexdigest()
            if content_hash in seen_hashes:
                continue  # skip duplicate
            seen_hashes.add(content_hash)
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

    # 🧼 Remove deeply redundant <div> layers
    cleaned_soup = unwrap_redundant_div_layers(cleaned_soup)
    # 🧹 Then remove duplicated blocks
    double_cleaned_soup = remove_duplicate_blocks(cleaned_soup)


    cleaned_soup = remove_all_before_tag(cleaned_soup, remove_all_before_this_tag_class_first_appear[0], remove_all_before_this_tag_class_first_appear[1])
    save_output_html(double_cleaned_soup, output_html_path)



if __name__ == '__main__':
    # Path to the local HTML file you want to process
    input_path = 'C:/Stuff/GIT/KTDash_converter/input.html'

    # Path where the cleaned output HTML will be saved
    output_path = 'C:/Stuff/GIT/KTDash_converter/extracted_output.html'

    # Run the extraction
    extract_clean_divs(input_path, output_path)