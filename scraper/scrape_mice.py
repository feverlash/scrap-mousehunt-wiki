import os
from pathlib import Path
from typing import Optional, Dict
from tqdm import tqdm

from scraper.config import MICE_DIR, MICE_CATEGORY
from scraper.api_client import WikiClient
from scraper.parser import sanitize_filename, parse_page_to_rag_markdown

def scrape_all_mice(
    client: WikiClient,
    limit: Optional[int] = None,
    force: bool = False
) -> Dict[str, int]:
    """
    Scrapes all mice from Category:Mice into structured Markdown documents.
    Includes automatic resume capability (skips already downloaded files unless force=True).
    """
    MICE_DIR.mkdir(parents=True, exist_ok=True)
    summary = {"downloaded": 0, "skipped": 0, "failed": 0}

    print(f"\n[MICE] Mulai scraping kategori Mice (Category:{MICE_CATEGORY})...")
    members = client.get_category_members(MICE_CATEGORY, cmtype="page", limit=limit)
    print(f"   Ditemukan {len(members)} tikus untuk diproses (Target: {MICE_DIR})")

    pbar = tqdm(members, desc="Mice", unit="mouse")
    for member in pbar:
        title = member["title"]
        filename = sanitize_filename(title)
        filepath = MICE_DIR / filename

        # Resume Check: skip if file already exists (unless force=True)
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
            entity_type="mouse",
            main_category="Mice"
        )

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(md_content)
            summary["downloaded"] += 1
        except Exception as e:
            print(f"[Error] Gagal menulis {filepath}: {e}")
            summary["failed"] += 1

        pbar.set_postfix({"done": summary["downloaded"], "skip": summary["skipped"]})

    print(f"\n[MICE SELESAI] Download: {summary['downloaded']}, Dilewati (sudah ada): {summary['skipped']}, Gagal: {summary['failed']}")
    return summary
