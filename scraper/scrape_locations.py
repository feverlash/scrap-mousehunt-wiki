import os
from pathlib import Path
from typing import Optional, Dict
from tqdm import tqdm

from scraper.config import LOCATIONS_DIR, LOCATIONS_CATEGORY
from scraper.api_client import WikiClient
from scraper.parser import sanitize_filename, parse_page_to_rag_markdown

def scrape_all_locations(
    client: WikiClient,
    limit: Optional[int] = None,
    force: bool = False
) -> Dict[str, int]:
    """
    Scrapes all locations from Category:Locations into structured Markdown documents.
    Excludes History and Trivia automatically.
    """
    LOCATIONS_DIR.mkdir(parents=True, exist_ok=True)
    summary = {"downloaded": 0, "skipped": 0, "failed": 0}

    print(f"\n[LOCATIONS] Mulai scraping kategori Locations (Category:{LOCATIONS_CATEGORY})...")
    members = client.get_category_members(LOCATIONS_CATEGORY, cmtype="page", limit=limit)
    print(f"   Ditemukan {len(members)} lokasi untuk diproses (Target: {LOCATIONS_DIR})")

    pbar = tqdm(members, desc="Locations", unit="loc")
    for member in pbar:
        title = member["title"]
        filename = sanitize_filename(title)
        filepath = LOCATIONS_DIR / filename

        # Resume Check
        if not force and filepath.exists() and filepath.stat().st_size > 50:
            summary["skipped"] += 1
            pbar.set_postfix({"skip": summary["skipped"], "done": summary["downloaded"]})
            continue

        page_data = client.get_page_data(title)
        if not page_data:
            summary["failed"] += 1
            continue

        md_content = parse_page_to_rag_markdown(
            parse_data=page_data,
            entity_type="location",
            main_category="Locations"
        )

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(md_content)
            summary["downloaded"] += 1
        except Exception as e:
            print(f"[Error] Gagal menulis {filepath}: {e}")
            summary["failed"] += 1

        pbar.set_postfix({"done": summary["downloaded"], "skip": summary["skipped"]})

    print(f"\n[LOCATIONS SELESAI] Download: {summary['downloaded']}, Dilewati: {summary['skipped']}, Gagal: {summary['failed']}")
    return summary
