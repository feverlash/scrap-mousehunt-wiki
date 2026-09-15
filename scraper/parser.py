import re
import yaml
from bs4 import BeautifulSoup
from typing import Dict, Any

from scraper.config import BASE_WIKI_URL

ALL_POWER_TYPES = [
    "Physical", "Tactical", "Hydro", "Arcane", "Forgotten",
    "Shadow", "Draconic", "Law", "Rift", "Parental"
]

def sanitize_filename(title: str) -> str:
    """Sanitize page title for Windows file system while maintaining legibility."""
    s = title.replace(":", " - ").replace("/", " - ").replace("\\", " - ")
    s = s.replace("|", "_")
    s = re.sub(r'[<>"\?\*]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return f"{s}.md"

def clean_text(text: str) -> str:
    """Clean extra spaces and wiki markup artifacts."""
    if not text:
        return ""
    text = re.sub(r'\[edit\]', '', text)
    text = text.replace('\xa0', ' ')
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def html_table_to_markdown(table: BeautifulSoup) -> str:
    """Convert an HTML table into a clean GitHub-Flavored Markdown table."""
    rows = table.find_all("tr")
    if not rows:
        return ""

    parsed_rows = []
    for tr in rows:
        cells = tr.find_all(["th", "td"])
        row_vals = [clean_text(c.get_text()).replace('\n', '<br>').replace('|', '&#124;') for c in cells]
        if any(v != '' for v in row_vals):
            parsed_rows.append(row_vals)

    if not parsed_rows:
        return ""

    max_cols = max(len(r) for r in parsed_rows)
    if max_cols == 0:
        return ""

    normalized = []
    for r in parsed_rows:
        if len(r) < max_cols:
            r = r + [''] * (max_cols - len(r))
        normalized.append(r)

    headers = normalized[0]
    if len(headers) == 1 and max_cols > 1:
        headers = headers + [''] * (max_cols - 1)

    md_lines = []
    md_lines.append("| " + " | ".join(headers) + " |")
    md_lines.append("| " + " | ".join(["---"] * max_cols) + " |")

    for r in normalized[1:]:
        md_lines.append("| " + " | ".join(r) + " |")

    return "\n" + "\n".join(md_lines) + "\n\n"

def parse_page_to_rag_markdown(parse_data: Dict[str, Any], entity_type: str, main_category: str) -> str:
    """
    Direct Wiki format: Headings follow Wiki 1:1, content follows Wiki 1:1.
    Includes clean YAML frontmatter and strips out unwanted image/edit sections.
    """
    title = parse_data.get("title", "")
    categories = [
        c["*"] for c in parse_data.get("categories", [])
        if not any(c["*"].startswith(prefix) for prefix in ["Pages_", "Articles_", "Incomplete", "Category:"])
    ]
    raw_html = parse_data.get("text", {}).get("*", "")

    soup = BeautifulSoup(raw_html, "html.parser")
    content = soup.find("div", class_="mw-parser-output") or soup

    # Decompose unwanted elements
    for el in content(["script", "style", "nav", "noscript", "form"]):
        el.decompose()
    for el in content.find_all(class_=["mw-editsection", "navbox", "catlinks", "toc", "printfooter"]):
        el.decompose()

    frontmatter = {
        "title": title,
        "type": entity_type,
        "category": main_category,
        "subcategories": categories,
        "wiki_url": f"{BASE_WIKI_URL}/{title.replace(' ', '_')}"
    }

    md_output = [
        "---",
        yaml.dump(frontmatter, sort_keys=False, allow_unicode=True).strip(),
        "---\n",
        f"# {title}\n"
    ]

    skip_section = False
    for el in content.children:
        if not el.name:
            continue

        # Headings
        if el.name in ["h2", "h3", "h4"]:
            heading_text = clean_text(el.get_text())
            heading_lower = heading_text.lower()
            # Skip image gallery, history and trivia, external links, and reference noise
            noise_headers = [
                "see also", "external links", "images", "references", "navigation",
                "history and trivia", "history", "trivia"
            ]
            if any(k in heading_lower for k in noise_headers):
                skip_section = True
                continue
            else:
                skip_section = False

            level = "#" * int(el.name[1])
            md_output.append(f"\n{level} {heading_text}\n")
            continue

        if skip_section:
            continue

        # Paragraphs & Blockquotes
        if el.name in ["p", "blockquote"]:
            txt = clean_text(el.get_text())
            if txt:
                md_output.append(f"{txt}\n")

        # Unordered Lists
        elif el.name == "ul":
            for li in el.find_all("li", recursive=False):
                txt = clean_text(li.get_text())
                if txt:
                    md_output.append(f"- {txt}")
            md_output.append("")

        # Ordered Lists
        elif el.name == "ol":
            for idx, li in enumerate(el.find_all("li", recursive=False), 1):
                txt = clean_text(li.get_text())
                if txt:
                    md_output.append(f"{idx}. {txt}")
            md_output.append("")

        # Tables (Infobox, Weaknesses, Shoppes, Recipes)
        elif el.name == "table":
            tbl_md = html_table_to_markdown(el)
            if tbl_md:
                md_output.append(tbl_md)

    return "\n".join(md_output)
