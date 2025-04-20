# KTDash_converter

This Python script extracts clean text from elements with specific class names in a local HTML file and outputs a new HTML file composed only of `<div>` tags containing the directly embedded text from those elements. It strips away all attributes, inner tags, and nested formatting, leaving only the human-readable content that appears **between** HTML tags.

---

## ✅ Features

- 🔍 Finds elements by their `class` attribute
- ✂️ Removes all nested child elements and tags
- 🧼 Only includes direct text content (ignores tags like `<i>`, `<sup>`, `<strong>`, etc.)
- 📄 Wraps each piece of text in a new `<div>`
- 🧱 Preserves structure: one `<div>` per matching tag
- 📤 Outputs a clean, readable HTML file with `<head>` and `<body>`

---

## 📂 Example

Given this input:
```html
<h3 class="tab-content">
  Grey Knights
  <sup><i class="icon"></i></sup>
</h3>
```

The output will be:
```html
<html>
 <head>
  <title>
   Extracted Divs
  </title>
 </head>
 <body>
  <div>
   Grey Knights
  </div>
 </body>
</html>
```

Even though the original element contains nested tags like `<sup>` and `<i>`, only the top-level text (`Grey Knights`) is kept.

---

## 🚀 How to Use

### 1. 📥 Install Dependencies

Only `beautifulsoup4` is required. Install it via pip:

```bash
pip install beautifulsoup4
```

---

### 2. 🛠 Configure the Script

Edit the bottom of the script to match your file paths and class names:

```python
input_path = 'C:/Stuff/input.html'  # Your input file
output_path = 'C:/Stuff/extracted_output.html'  # Output file
class_names = ['tab-content']  # List of class names to extract
```

You can include multiple class names like this:

```python
class_names = ['tab-content', 'section-header', 'highlight']
```

---

### 3. ▶️ Run the Script

Run the Python file in your terminal or editor:

```bash
python html_extract.py
```

The output will be saved to the file path you specified.

---

## 🧪 What It Does

This script:
- Opens the input HTML file
- Looks for all elements matching the given class names
- For each matching element:
  - Extracts only the text directly between its tags
  - Ignores all inner HTML, formatting tags, icons, etc.
  - Wraps the text in a plain `<div>`
- Writes a new HTML file with just those text blocks

---

## 🛠 Use Cases

- Extracting readable text from complex, JS-heavy HTML exports
- Cleaning up HTML for downstream processing or NLP
- Simplifying dashboards, reports, or CMS output for documentation
- Creating summary views of HTML content

---

## 📎 Notes

- Only direct text is included. Nested content inside tags (like `<sup>`, `<span>`, or `<i>`) is ignored.
- The output is intended for **clean reading and processing**, not for preserving visual structure.
- If you need full inner text (including children), or want to keep tags like `<strong>` or `<em>`, the script can be easily adjusted.

---

## 📄 License

This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

In jurisdictions that recognize copyright laws, the author or authors
of this software dedicate any and all copyright interest in the
software to the public domain. We make this dedication for the benefit
of the public at large and to the detriment of our heirs and
successors. We intend this dedication to be an overt act of
relinquishment in perpetuity of all present and future rights to this
software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <http://unlicense.org/>

---

Happy scraping! 🕵️‍♂️
