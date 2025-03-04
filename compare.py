import os
import json
import xml.etree.ElementTree as ET
import datetime

def flatten_json(data, parent_key=""):
    """Recursively traverse a JSON object (dict/list) to produce
    a list of (field_path, value) pairs."""
    entities = []
    if isinstance(data, dict):
        for k, v in data.items():
            full_key = f"{parent_key}.{k}" if parent_key else k
            entities.extend(flatten_json(v, full_key))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            full_key = f"{parent_key}[{i}]"
            entities.extend(flatten_json(item, full_key))
    else:
        val_str = str(data) if data is not None else ""
        entities.append((parent_key, val_str))
    return entities

def flatten_xml(element, parent_key=""):
    """Recursively traverse XML to produce a list of (field_path, value) pairs."""
    entities = []
    text_value = (element.text or "").strip()
    if text_value:
        field_key = f"{parent_key}.{element.tag}" if parent_key else element.tag
        entities.append((field_key, text_value))

    for child in element:
        full_key = f"{parent_key}.{element.tag}" if parent_key else element.tag
        entities.extend(flatten_xml(child, full_key))

    return entities

def parse_json_entities(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return flatten_json(data)

def parse_xml_entities(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    return flatten_xml(root)

def evaluate_entities(json_entities, xml_entities):
    """
    Compare lists of (key, value) pairs from JSON and XML.
    Remove "Auftrag." prefix from each XML entity key.
    Returns (total_json_entities, correct_matches, transformed_xml).
    """
    set_json = set(json_entities)

    # Transform the XML list to remove "Auftrag." prefix
    transformed_xml = []
    for (key, val) in xml_entities:
        if key.startswith("Auftrag."):
            new_key = key[len("Auftrag."):]
        else:
            new_key = key
        transformed_xml.append((new_key, val))

    set_xml = set(transformed_xml)

    total_json_entities = len(json_entities)
    correct = len(set_json.intersection(set_xml))
    return total_json_entities, correct, transformed_xml

def main(output_dir="output", reference_dir="reference"):
    # Gather .json files
    json_files = [f for f in os.listdir(output_dir) if f.lower().endswith(".json")]
    # Optional: sort them to have a consistent next/prev order
    json_files.sort()

    # Prepare a timestamped folder under "reports"
    now_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    master_report_dir = os.path.join("reports", now_str)
    os.makedirs(master_report_dir, exist_ok=True)

    # We will store all results in memory so we can generate next/prev links
    all_details = []  # each entry will hold: base_name, total, correct, json_dict, xml_dict

    # --- PASS 1: Parse all files, store data in memory ---
    for json_file in json_files:
        base_name_full = os.path.splitext(json_file)[0]
        # Possibly remove first 8 chars if needed
        base_name = base_name_full[8:]

        json_path = os.path.join(output_dir, json_file)
        xml_file = base_name + ".xml"
        xml_path = os.path.join(reference_dir, xml_file)

        if not os.path.exists(xml_path):
            print(f"Keine Referenzdatei für {json_file} gefunden – überspringe.")
            continue

        json_ents = parse_json_entities(json_path)
        xml_ents = parse_xml_entities(xml_path)
        total, correct, transformed_xml = evaluate_entities(json_ents, xml_ents)

        # Convert to dict for easier row-by-row comparison
        json_dict = dict(json_ents)
        xml_dict = dict(transformed_xml)

        all_details.append({
            "base_name": base_name,
            "json_dict": json_dict,
            "xml_dict": xml_dict,
            "total": total,
            "correct": correct
        })

    # --- PASS 2: Generate detail pages and the master summary ---
    # Create the subdirectories and detail pages
    for i, detail_info in enumerate(all_details):
        base_name = detail_info["base_name"]
        json_dict = detail_info["json_dict"]
        xml_dict = detail_info["xml_dict"]

        # Next/Prev references
        prev_link = None
        next_link = None

        if i > 0:
            prev_name = all_details[i-1]["base_name"]
            # details.html is always "details.html" in that subfolder
            prev_link = f"../{prev_name}/details.html"
        if i < len(all_details) - 1:
            next_name = all_details[i+1]["base_name"]
            next_link = f"../{next_name}/details.html"

        file_report_dir = os.path.join(master_report_dir, base_name)
        os.makedirs(file_report_dir, exist_ok=True)

        # Build a details.html that shows each (key, json_value) vs. (key, xml_value)
        all_keys = sorted(set(json_dict.keys()) | set(xml_dict.keys()))

        detail_lines = []
        detail_lines.append("<!DOCTYPE html>")
        detail_lines.append("<html>")
        detail_lines.append("  <head>")
        detail_lines.append("    <meta charset='utf-8'>")
        detail_lines.append(f"    <title>Details for {base_name}</title>")
        detail_lines.append("""    <style>
            body {
              font-family: Arial, sans-serif;
              margin: 20px;
            }
            table {
              border-collapse: collapse;
              margin-top: 10px;
              width: 90%;
            }
            th, td {
              border: 1px solid #aaa;
              padding: 8px;
              text-align: left;
            }
            nav {
                    position: sticky;
                    top: 0;
                    background-color: white;
                    padding-bottom: 3px;
                    border-bottom: 1px solid #ccc;
            }
            th {
              background-color: #f2f2f2;
            }
            h1 {
              font-size: 1.5em;

            }
            .mismatch {
              border: 2px solid red;
            }
            .nav-links {
              margin: 10px 0;
            }
            .nav-links a {
              margin-right: 15px;
              text-decoration: none;
              color: blue;
            }
        </style>""")
        detail_lines.append("  </head>")
        detail_lines.append("  <body>")

        # Navigation links at the top
        detail_lines.append('    <nav><div class="nav-links">')
        if prev_link:
            detail_lines.append(f'      <a href="{prev_link}">&larr; Previous</a>')
        detail_lines.append(f'      <a href="../report.html"> &uarr; Up</a>')
        if next_link:
            detail_lines.append(f'      <a href="{next_link}">Next &rarr;</a>')
        detail_lines.append("    </div>")

        detail_lines.append(f"    <h1>Details for {base_name} [<a href='../../../input/Auftrag {base_name}.pdf'>PDF</a>]</h1></nav>")
        detail_lines.append("    <table>")
        detail_lines.append("      <tr><th>Key</th><th>JSON Value</th><th>XML Value</th></tr>")

        for key in all_keys:
            val_json = json_dict.get(key, "")
            val_xml = xml_dict.get(key, "")

            # If the values do not match, apply a "mismatch" CSS class
            if val_json != val_xml:
                td_json_class = "mismatch"
                td_xml_class = "mismatch"
            else:
                td_json_class = ""
                td_xml_class = ""

            detail_lines.append(
                f"      <tr>"
                f"<td>{key}</td>"
                f"<td class='{td_json_class}'>{val_json}</td>"
                f"<td class='{td_xml_class}'>{val_xml}</td>"
                f"</tr>"
            )

        detail_lines.append("    </table>")

        # Navigation links at the bottom
        detail_lines.append('    <div class="nav-links">')
        if prev_link:
            detail_lines.append(f'      <a href="{prev_link}">&larr; Previous</a>')
        if next_link:
            detail_lines.append(f'      <a href="{next_link}">Next &rarr;</a>')
        detail_lines.append("    </div>")

        detail_lines.append("  </body>")
        detail_lines.append("</html>")

        details_html_path = os.path.join(file_report_dir, "details.html")
        with open(details_html_path, "w", encoding="utf-8") as f:
            f.write("\n".join(detail_lines))
        print(f"Details report written to {details_html_path}")

    # Finally, create a master report with the summary table
    master_report_path = os.path.join(master_report_dir, "report.html")
    html_content = []
    html_content.append("<!DOCTYPE html>")
    html_content.append("<html>")
    html_content.append("  <head>")
    html_content.append("    <meta charset='utf-8'>")
    html_content.append("    <title>Evaluation Summary</title>")
    html_content.append("""    <style>
        body {
          font-family: Arial, sans-serif;
          margin: 20px;
        }
        table {
          border-collapse: collapse;
          margin-top: 10px;
          width: 80%;
        }
        th, td {
          border: 1px solid #aaa;
          padding: 8px;
          text-align: left;
        }
        th {
          background-color: #f2f2f2;
        }
        h1 {
          font-size: 1.5em;
        }
      </style>""")
    html_content.append("  </head>")
    html_content.append("  <body>")
    html_content.append("    <h1>Evaluation Summary</h1>")
    html_content.append("    <table>")
    html_content.append("      <tr><th>Datei</th><th>Anzahl Entities</th><th>Korrekte Werte</th><th>Detail-Link</th></tr>")

    for detail_info in all_details:
        name = detail_info["base_name"]
        total = detail_info["total"]
        corr = detail_info["correct"]
        link_path = f"./{name}/details.html"
        html_content.append(
            f"      <tr>"
            f"<td>{name}</td>"
            f"<td>{total}</td>"
            f"<td>{corr}</td>"
            f"<td><a href='{link_path}'>Details</a></td>"
            f"</tr>"
        )

    html_content.append("    </table>")
    html_content.append(f"    <p>Generated on: {now_str}</p>")
    html_content.append("  </body>")
    html_content.append("</html>")

    with open(master_report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html_content))

    print(f"Master report written to {master_report_path}")
    print("Done!")

# -------------------------
#   Script entry point
# -------------------------
if __name__ == "__main__":
    main()
