from bs4 import BeautifulSoup, Tag, Comment, NavigableString
import re

def clean_text(text):
    if not text:
        return ''
    # Replace multiple whitespace (spaces, newlines, tabs) with a single space
    cleaned = re.sub(r'\s+', ' ', text)
    return cleaned.strip()


def clean_to_div_tree(element, soup):
    """
    Recursively converts an element and its children to a tree of <div>s with only text.
    """
    div = soup.new_tag("div")

    if element.string and element.string.strip():
        div.string = clean_text(element.string)
    else:
        for child in element.children:
            if isinstance(child, str):
                if child.strip():
                    text_div = soup.new_tag("div")
                    text_div.string = clean_text(child)
                    div.append(text_div)
            elif isinstance(child, Tag):
                div.append(clean_to_div_tree(child, soup))
    
    return div

def extract_clean_divs(input_html_path, class_names, output_html_path):
    with open(input_html_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')

    new_soup = BeautifulSoup('''<html><head><title>Extracted Divs</title><style>body {background-color: #1e1e1e;color: #f0f0f0;font-family: sans-serif;padding: 20px;}div {margin-bottom: 1em;}</style></head><body></body></html>''', 'html.parser')
    new_body = new_soup.body

    for class_name in class_names:
        elements = soup.find_all(class_=class_name)
        for el in elements:
            # Skip elements that have no visible text in them or their children
            has_visible_text = any(
                isinstance(child, NavigableString) and not isinstance(child, Comment) and child.strip()
                for child in el.descendants
            )
            if not has_visible_text:
                continue

            clean_div = clean_to_div_tree(el, new_soup)
            if clean_div:
                new_body.append(clean_div)

    with open(output_html_path, 'w', encoding='utf-8') as file:
        file.write(new_soup.prettify())

# Example usage
if __name__ == '__main__':
    input_path = 'C:/Stuff/GIT/KTDash_converter/input.html'
    output_path = 'C:/Stuff/GIT/KTDash_converter/extracted_output.html'
    class_names = ['pointer', 'tab-pane']  # Replace with desired class names

    extract_clean_divs(input_path, class_names, output_path)
