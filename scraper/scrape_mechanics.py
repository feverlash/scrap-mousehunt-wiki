import os
from pathlib import Path
from typing import Optional, Dict
from tqdm import tqdm

from scraper.config import MECHANICS_DIR, CORE_MECHANICS_PAGES, FUNCTIONAL_SKINS
from scraper.api_client import WikiClient
from scraper.parser import sanitize_filename, parse_page_to_rag_markdown

def scrape_core_mechanics(
    client: WikiClient,
    force: bool = False
) -> Dict[str, int]:
    """
    Scrapes core gameplay mechanics, progression systems, and functional stat skins.
    """
    MECHANICS_DIR.mkdir(parents=True, exist_ok=True)
    summary = {"downloaded": 0, "skipped": 0, "failed": 0}

    targets = [("mechanic", title) for title in CORE_MECHANICS_PAGES] + [("functional_skin", title) for title in FUNCTIONAL_SKINS]

    print(f"\n[MECHANICS] Mulai scraping konsep & mekanik inti ({len(targets)} halaman)...")
    pbar = tqdm(targets, desc="Mechanics", unit="page")

    for cat_type, title in pbar:
        filename = sanitize_filename(title)
        filepath = MECHANICS_DIR / filename

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
            entity_type=cat_type,
            main_category="Gameplay Mechanics"
        )

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(md_content)
            summary["downloaded"] += 1
        except Exception as e:
            print(f"[Error] Gagal menulis {filepath}: {e}")
            summary["failed"] += 1

        pbar.set_postfix({"done": summary["downloaded"], "skip": summary["skipped"]})

    print(f"\n[MECHANICS SELESAI] Download: {summary['downloaded']}, Dilewati: {summary['skipped']}, Gagal: {summary['failed']}")
    return summary
