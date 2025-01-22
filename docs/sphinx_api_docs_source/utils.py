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

    properties = soup.select(".py.property")
    if properties:
        # Add h2 title to Properties section
        add_section_title(soup, properties, "Properties")

        # Display properties as table
        table = soup.new_tag("table")
        tbody = soup.new_tag("tbody")

        create_header_row(soup, table)

        for prop in properties:
            create_row(soup, tbody, prop)

        table.append(tbody)
        parent_div = soup.select("#properties")[0]
        parent_div.append(table)


def add_section_title(soup, items, title):
    wrapper_div = soup.new_tag("div")
    wrapper_div.attrs["id"] = title.lower()
    title_h2 = soup.new_tag("h2")
    title_h2.string = title
    parent = items[0].parent

    for item in items:
        wrapper_div.append(item.extract())

    wrapper_div.insert(0, "\r\n")
    wrapper_div.insert(1, title_h2)
    wrapper_div.insert(2, "\r\n")
    parent.insert_after(wrapper_div)


def create_header_row(soup, table):
    thead = soup.new_tag("thead")
    thead_row = soup.new_tag("tr")

    column_names = ["Name", "Description", "Reference"]

    for column_name in column_names:
        new_cell = soup.new_tag("th")
        new_cell.append(column_name)
        thead_row.append(new_cell)

    thead.append(thead_row)

    table.append(thead)
    table.append("\r\n")
    table.insert(0, "\r\n")


def create_row(soup, tbody, prop):
    new_row = soup.new_tag("tr")
    reference_link = prop.select("a")[0]
    reference_link.string = reference_link.text.split(".")[-1]

    columns = [
        "`" + prop.select(".descname")[0].get_text() + "`",
        prop.select("dd")[0].get_text(),
        reference_link,
    ]

    for column in columns:
        new_cell = soup.new_tag("td")
        new_cell.append("\r\n")
        new_cell.append(column)
        new_cell.append("\r\n")
        new_row.append(new_cell)

    tbody.append(new_row)
    prop.extract()
