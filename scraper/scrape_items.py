import os
from pathlib import Path
from typing import Optional, Dict
from tqdm import tqdm

from scraper.config import ITEMS_DIR, ITEM_CATEGORIES
from scraper.api_client import WikiClient
from scraper.parser import sanitize_filename, parse_page_to_rag_markdown

def scrape_all_items(
    client: WikiClient,
    limit_per_category: Optional[int] = None,
    specific_category: Optional[str] = None,
    force: bool = False
) -> Dict[str, int]:
    """
    Scrapes item categories in sequence, saving each as a structured Markdown file.
    Includes automatic resume capability (skips already downloaded files unless force=True).
    """
    ITEMS_DIR.mkdir(parents=True, exist_ok=True)
    summary = {"downloaded": 0, "skipped": 0, "failed": 0}

    categories_to_run = (
        {specific_category: ITEM_CATEGORIES[specific_category]}
        if specific_category and specific_category in ITEM_CATEGORIES
        else ITEM_CATEGORIES
    )

    print(f"\n[ITEMS] Mulai scraping kategori item (Total {len(categories_to_run)} kategori)...")

    for cat_name, subfolder in categories_to_run.items():
        target_dir = ITEMS_DIR / subfolder
        target_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n-> Mengambil daftar item untuk: Category:{cat_name}")
        members = client.get_category_members(cat_name, cmtype="page", limit=limit_per_category)
        print(f"   Ditemukan {len(members)} item (Target: {target_dir})")

        pbar = tqdm(members, desc=f"Item [{cat_name}]", unit="item")
        for member in pbar:
            title = member["title"]
            filename = sanitize_filename(title)
            filepath = target_dir / filename

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
                entity_type=subfolder,
                main_category=cat_name
            )

            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(md_content)
                summary["downloaded"] += 1
            except Exception as e:
                print(f"[Error] Gagal menulis {filepath}: {e}")
                summary["failed"] += 1

            pbar.set_postfix({"done": summary["downloaded"], "skip": summary["skipped"]})

    print(f"\n[ITEMS SELESAI] Download: {summary['downloaded']}, Dilewati (sudah ada): {summary['skipped']}, Gagal: {summary['failed']}")
    return summary
