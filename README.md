# KTDash_converter

This Python script extracts human-readable text from specific HTML elements in a local `.html` file, based on provided class names. It outputs a clean and minimal HTML file where each matched element is represented as a simple `<div>` containing only the **direct** text content (ignoring text inside nested child elements).

## ✅ Features

- Parses local HTML files using BeautifulSoup
- Finds elements by their `class` attribute
- Strips away all HTML tags except outer `<div>`
- Only includes text **directly between tags** (ignores nested tags like `<i>`, `<sup>`, etc.)
- Outputs clean HTML structure with a `<head>` and `<body>`

## 📂 Example

Given this input:
```html
<h3 class="tab-content">
  Grey Knights
  <sup><i class="icon"></i></sup>
</h3>
