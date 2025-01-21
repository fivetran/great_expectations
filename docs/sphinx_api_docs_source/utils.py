def apply_markdown_adjustments(soup, html_file_path, html_file_contents):  # noqa: C901
    # Add newline before closing dt tags when they have more than one child
    for item in soup.find_all("dt"):
        lengthChildren = len(item.findChildren())
        if lengthChildren > 1:
            item.append("\r\n")
        if "Relevant Documentation Links" in item.get_text():
            item.string.replaceWith(item.get_text().replace("-", "").strip())

    # Add newline before closing th, td and li tags
    for item in soup.find_all(["th", "td", "li"]):
        item.append("\r\n")

    # Add newline after opening pre, dd and li tags
    for item in soup.find_all(["pre", "dd", "li"]):
        item.insert(0, "\r\n")

    # Add newline before opening dd and p tags
    for item in soup.find_all(["dd", "p"]):
        item.insert_before("\r\n")

    # Add newline before closing cite tag
    if "ConfiguredAssetFilesystemDataConnector" in str(html_file_path):
        for item in soup.find_all("cite"):
            item.append("\r\n")

    # Replace asterisk character with corresponding HTML entity
    for item in soup.find_all("span"):
        if item and item.string and "*" in item.get_text():
            item.string.replaceWith(item.get_text().replace("*", "&#42;"))

    # Add newline after opening p tag and before closing p tags when they have children
    for item in soup.find_all("p"):
        lengthChildren = len(item.findChildren())
        if lengthChildren > 0:
            item.insert(0, "\r\n")
            item.append("\r\n")


def apply_structure_changes(soup, html_file_path, html_file_contents):
    # Add h2 title to Methods section
    methods = soup.select(".py.method")
    if methods:
        add_section_title(soup, methods, "Methods")

    # Add h2 title to Properties section
    properties = soup.select(".py.property")
    if properties:
        add_section_title(soup, properties, "Properties")


def add_section_title(soup, items, title):
    wrapper_div = soup.new_tag("div")
    title_h2 = soup.new_tag("h2")
    title_h2.string = title
    parent = items[0].parent

    for item in items:
        wrapper_div.append(item.extract())

    wrapper_div.insert(0, "\r\n")
    wrapper_div.insert(1, title_h2)
    wrapper_div.insert(2, "\r\n")
    parent.insert_after(wrapper_div)
