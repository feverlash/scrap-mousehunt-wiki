import re
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from bs4 import BeautifulSoup

def replace_em_dashes(text: str) -> str:
    """Replace any em-dashes or en-dashes with standard hyphens."""
    if not text:
        return ""
    return text.replace("—", "-").replace("–", "-")

def clean_lore_text(text: str) -> str:
    """Clean extra spaces, wiki markup artifacts, and normalize dashes."""
    if not text:
        return ""
    text = re.sub(r'\[edit\]', '', text)
    text = text.replace('\xa0', ' ')
    text = replace_em_dashes(text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

from scraper.parser import html_table_to_markdown

def parse_wiki_page_for_lore(parse_data: Dict[str, Any], entity_type: str, component_code: str) -> str:
    """
    Parses raw MediaWiki API HTML response into clean, narrative-focused Lore Markdown.
    Preserves story text, infobox lore, dialogue, tables, and removes cosmetic/patch noise.
    """
    title = parse_data.get("title", "")
    title = replace_em_dashes(title)
    categories = [
        replace_em_dashes(c["*"]) for c in parse_data.get("categories", [])
        if not any(c["*"].startswith(prefix) for prefix in ["Pages_", "Articles_", "Incomplete", "Category:"])
    ]
    raw_html = parse_data.get("text", {}).get("*", "")
    soup = BeautifulSoup(raw_html, "html.parser")
    content = soup.find("div", class_="mw-parser-output") or soup

    # Remove unwanted UI elements
    for el in content(["script", "style", "nav", "noscript", "form"]):
        el.decompose()
    for el in content.find_all(class_=["mw-editsection", "navbox", "catlinks", "toc", "printfooter"]):
        el.decompose()

    frontmatter = {
        "title": title,
        "component": component_code,
        "type": entity_type,
        "categories": categories,
        "wiki_url": f"https://mhwiki.hitgrab.com/wiki/index.php/{title.replace(' ', '_')}"
    }

    md_lines = [
        "---",
        yaml.dump(frontmatter, sort_keys=False, allow_unicode=True).strip(),
        "---\n",
        f"# {title}\n"
    ]

    skip_section = False
    for el in content.children:
        if not el.name:
            continue

        if el.name in ["h2", "h3", "h4"]:
            h_text = clean_lore_text(el.get_text())
            h_lower = h_text.lower()
            # Skip purely technical/patch sections
            technical_noise = [
                "see also", "external links", "images", "references", "navigation",
                "patch history", "version history", "release history"
            ]
            if any(k in h_lower for k in technical_noise):
                skip_section = True
                continue
            else:
                skip_section = False

            level = "#" * int(el.name[1])
            md_lines.append(f"\n{level} {h_text}\n")
            continue

        if skip_section:
            continue

        if el.name in ["p", "blockquote"]:
            txt = clean_lore_text(el.get_text())
            if txt:
                if el.name == "blockquote":
                    md_lines.append(f"> {txt}\n")
                else:
                    md_lines.append(f"{txt}\n")

        elif el.name in ["dl", "dd", "dt"]:
            txt = clean_lore_text(el.get_text())
            if txt:
                md_lines.append(f"> {txt}\n")

        elif el.name == "table":
            tbl_md = html_table_to_markdown(el)
            if tbl_md:
                md_lines.append(tbl_md)

        elif el.name == "div":
            inner_tables = el.find_all("table")
            if inner_tables:
                for tbl in inner_tables:
                    tbl_md = html_table_to_markdown(tbl)
                    if tbl_md:
                        md_lines.append(tbl_md)
            else:
                txt = clean_lore_text(el.get_text())
                if txt and len(txt) > 15:
                    md_lines.append(f"{txt}\n")

        elif el.name == "ul":
            for li in el.find_all("li", recursive=False):
                txt = clean_lore_text(li.get_text())
                if txt:
                    md_lines.append(f"- {txt}")
            md_lines.append("")

        elif el.name == "ol":
            for idx, li in enumerate(el.find_all("li", recursive=False), 1):
                txt = clean_lore_text(li.get_text())
                if txt:
                    md_lines.append(f"{idx}. {txt}")
            md_lines.append("")

    return "\n".join(md_lines)


def extract_mouse_lore_from_file(file_path: Path) -> Optional[str]:
    """Extracts rich narrative lore from a mouse markdown file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return None

    content = replace_em_dashes(content)
    title = file_path.stem

    # Extract Group
    group_match = re.search(r"\|\s*Mouse Group:\s*([^|\n]+)", content, re.IGNORECASE)
    mouse_group = group_match.group(1).strip() if group_match else "Unknown Faction"

    # Extract Points & Gold
    stats_match = re.search(r"\|\s*Points:\s*\|\s*([^|\n]+)\s*\|\s*Gold:\s*\|\s*([^|\n]+)", content, re.IGNORECASE)
    points = stats_match.group(1).strip() if stats_match else "N/A"
    gold = stats_match.group(2).strip() if stats_match else "N/A"

    # Extract Power Types
    power_match = re.search(r"\|\s*Required Power Types:\s*\|\s*([^|\n]+)", content, re.IGNORECASE)
    power_types = power_match.group(1).strip() if power_match else "Any"

    # Extract Cheese & Charm
    cheese_match = re.search(r"\|\s*Cheese:\s*\|\s*([^|\n]+)\s*\|\s*Charm:\s*\|\s*([^|\n]+)", content, re.IGNORECASE)
    cheese = cheese_match.group(1).strip() if cheese_match else "Standard"
    charm = cheese_match.group(2).strip() if cheese_match else "None"

    # Extract Locations & Loot
    loc_match = re.search(r"\|\s*Locations:\s*\|\s*([^|\n]+)\s*\|\s*Loot:\s*\|\s*([^|\n]+)", content, re.IGNORECASE)
    locations = loc_match.group(1).strip() if loc_match else "Gnawnia"
    loot = loc_match.group(2).strip() if loc_match else "None"

    # Extract Lore Quote (Flavor text in table after Larry's Loot Lexicon)
    lore_match = re.search(r"\|\s*Larry's Loot Lexicon:.*?\|\s*\n\|\s*(.+?)\s*\|\s*\|\s*\|\s*\|\s*\n", content, re.DOTALL)
    lore_text = ""
    if lore_match:
        lore_text = clean_lore_text(lore_match.group(1))

    # Also extract cheese preference section if available
    pref_match = re.search(r"## Cheese and Charm Preference\s*\n\s*(.+?)(?=\n##|\Z)", content, re.DOTALL)
    pref_text = clean_lore_text(pref_match.group(1)) if pref_match else ""

    # Extract weaknesses table / text if available
    weakness_match = re.search(r"## Power Type Weaknesses\s*\n\s*(.+?)(?=\n##|\Z)", content, re.DOTALL)
    weakness_text = clean_lore_text(weakness_match.group(1)) if weakness_match else ""

    frontmatter = {
        "title": title,
        "component": "B_mice_lore",
        "faction_group": mouse_group,
        "power_types": power_types,
        "habitat": locations,
        "cheese": cheese,
        "points": points,
        "gold": gold
    }

    md = [
        "---",
        yaml.dump(frontmatter, sort_keys=False, allow_unicode=True).strip(),
        "---\n",
        f"# 🐭 {title}\n",
        f"> **Group / Faction**: {mouse_group}  ",
        f"> **Primary Habitat**: {locations}  ",
        f"> **Vulnerable To**: {power_types}  ",
        f"> **Favored Bait**: {cheese}  ",
        f"> **Reward Tier**: {points} Points | {gold} Gold\n",
        "## 📜 Lore & Persona\n"
    ]

    if lore_text:
        md.append(f"> \"{lore_text}\"\n")
    else:
        md.append(f"*{title} adalah spesies tikus unik yang mendiami kawasan {locations}.*\n")

    if pref_text:
        md.append("## 🧀 Kebiasaan Umpan & Perilaku Berburu")
        md.append(f"{pref_text}\n")

    if loot and loot != "None":
        md.append("## 💎 Rampasan Berharga (Loot Drops)")
        md.append(f"- **Drop Items**: {loot}\n")

    return "\n".join(md)

def extract_equipment_lore_from_file(file_path: Path, eq_type: str) -> Optional[str]:
    """Extracts lore and engineering background from a weapon or base markdown file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return None

    content = replace_em_dashes(content)
    title = file_path.stem

    # Extract Power Type
    pt_match = re.search(r"Power Type:\s*([^|\n]+)", content, re.IGNORECASE)
    power_type = pt_match.group(1).strip() if pt_match else "General"

    # Extract Power & Luck
    power_match = re.search(r"\|\s*Power:\s*\|\s*([^|\n]+)", content, re.IGNORECASE)
    power = power_match.group(1).strip() if power_match else "N/A"

    luck_match = re.search(r"\|\s*Luck:\s*\|\s*([^|\n]+)", content, re.IGNORECASE)
    luck = luck_match.group(1).strip() if luck_match else "N/A"

    rank_match = re.search(r"\|\s*(?:Title Required|Rank requirement):\s*\|\s*([^|\n]+)", content, re.IGNORECASE)
    rank = rank_match.group(1).strip() if rank_match else "None"

    cost_match = re.search(r"\|\s*Cost:\s*\|\s*([^|\n]+)", content, re.IGNORECASE)
    cost = cost_match.group(1).strip() if cost_match else "N/A"

    # Extract Lore Quote (Flavor text in table after Larry's Loot Lexicon)
    lore_match = re.search(r"\|\s*Larry's Loot Lexicon:.*?\|\s*\n\|\s*(.+?)\s*\|\s*\|\s*\|\s*\|\s*\n", content, re.DOTALL)
    lore_text = ""
    if lore_match:
        lore_text = clean_lore_text(lore_match.group(1))

    # Extract Obtained Via
    obtained_match = re.search(r"## Obtained Via\s*\n\s*(.+?)(?=\n##|\Z)", content, re.DOTALL)
    obtained_text = clean_lore_text(obtained_match.group(1)) if obtained_match else ""

    frontmatter = {
        "title": title,
        "component": "C_equipment_lore",
        "category": eq_type,
        "power_type": power_type,
        "power": power,
        "luck": luck,
        "rank_required": rank
    }

    icon = "⚔️" if eq_type == "weapon" else "🛡️"
    md = [
        "---",
        yaml.dump(frontmatter, sort_keys=False, allow_unicode=True).strip(),
        "---\n",
        f"# {icon} {title}\n",
        f"> **Classification**: {power_type} {eq_type.capitalize()}  ",
        f"> **Power / Luck**: {power} Power | {luck} Luck  ",
        f"> **Title Requirement**: {rank}  ",
        f"> **Acquisition Cost**: {cost}\n",
        "## 📜 Lore & Rekayasa Perangkap\n"
    ]

    if lore_text:
        # replace any HTML br with newline
        lore_cleaned = lore_text.replace("<br>", "\n> ")
        md.append(f"> {lore_cleaned}\n")
    else:
        md.append(f"*{title} adalah perlengkapan berburu tipe {power_type} yang digunakan para pemburu di Kerajaan Gnawnia.*\n")

    if obtained_text:
        md.append("## 🔨 Asal-Usul & Perakitan (Crafting/Shoppe)")
        md.append(f"{obtained_text}\n")

    return "\n".join(md)

def extract_location_lore_from_file(file_path: Path) -> Optional[str]:
    """Extracts narrative worldbuilding, environment lore, and Larry's tips from a location file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return None

    content = replace_em_dashes(content)
    title = file_path.stem

    # Extract Region
    region_match = re.search(r"\|\s*Region:\s*([^|\n]+)", content, re.IGNORECASE)
    region = region_match.group(1).strip() if region_match else "Gnawnia"

    # Extract Minimum Rank
    rank_match = re.search(r"\|\s*Minimum Rank:\s*\|\s*([^|\n]+)", content, re.IGNORECASE)
    rank = rank_match.group(1).strip() if rank_match else "Recruit"

    # Extract Shops
    shops_match = re.search(r"\|\s*Shops:\s*\|\s*([^|\n]+)", content, re.IGNORECASE)
    shops = shops_match.group(1).strip() if shops_match else "None"

    # Extract Overview
    overview_match = re.search(r"## Overview\s*\n\s*(.+?)(?=\n##|\Z)", content, re.DOTALL)
    overview_text = clean_lore_text(overview_match.group(1)) if overview_match else ""

    # Extract Larry's Tips
    larry_match = re.search(r"### Hunting tips by Larry\s*\n\s*(.+?)(?=\n##|\Z)", content, re.DOTALL)
    larry_text = clean_lore_text(larry_match.group(1)) if larry_match else ""

    # Extract HUD / Environmental mechanics
    hud_match = re.search(r"## HUD\s*\n\s*(.+?)(?=\n##|\Z)", content, re.DOTALL)
    hud_text = clean_lore_text(hud_match.group(1)) if hud_match else ""

    frontmatter = {
        "title": title,
        "component": "D_world_regions",
        "region": region,
        "min_rank": rank,
        "shops": shops
    }

    md = [
        "---",
        yaml.dump(frontmatter, sort_keys=False, allow_unicode=True).strip(),
        "---\n",
        f"# 📍 {title}\n",
        f"> **Wilayah / Region**: {region}  ",
        f"> **Pangkat Minimal**: {rank}  ",
        f"> **Fasilitas Lokal**: {shops}\n",
        "## 🌍 Gambaran & Atmosfer Lingkungan\n"
    ]

    if overview_text:
        md.append(f"{overview_text}\n")
    else:
        md.append(f"*{title} adalah kawasan perburuan penting di kawasan {region}.*\n")

    if larry_text:
        md.append("## 🗣️ Nasihat & Pesan dari Larry the Knight\n")
        md.append(f"> \"{larry_text}\"\n")

    if hud_text:
        md.append("## ⚠️ Bahaya Lingkungan & Mekanik Wilayah")
        # Keep first 1200 chars if excessively long
        shortened_hud = hud_text[:1200] + ("..." if len(hud_text) > 1200 else "")
        md.append(f"{shortened_hud}\n")

    return "\n".join(md)

def extract_mechanic_lore_from_file(file_path: Path) -> Optional[str]:
    """Extracts world rules and mechanics narrative."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return None

    content = replace_em_dashes(content)
    title = file_path.stem

    frontmatter = {
        "title": title,
        "component": "F_world_mechanics"
    }

    # Remove existing frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            body = parts[2].strip()
        else:
            body = content
    else:
        body = content

    body = clean_lore_text(body)

    md = [
        "---",
        yaml.dump(frontmatter, sort_keys=False, allow_unicode=True).strip(),
        "---\n",
        f"# ⚙️ {title}\n",
        f"> **Hukum Dunia / Mekanik Cerita**: {title}\n",
        "## 📜 Konsep Lore & Aturan Permainan\n",
        body
    ]

    return "\n".join(md)
