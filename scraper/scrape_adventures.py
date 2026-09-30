import os
from pathlib import Path
from typing import Optional, Dict, List
from tqdm import tqdm

from scraper.config import ADVENTURES_DIR, ADVENTURE_BOOK_PAGE, ADVENTURES_CATEGORY
from scraper.api_client import WikiClient
from scraper.parser import sanitize_filename, parse_page_to_rag_markdown

def scrape_all_adventures(
    client: WikiClient,
    limit: Optional[int] = None,
    force: bool = False
) -> Dict[str, int]:
    """
    Scrapes the Adventure Book and all individual adventure quest pages.
    Saves clean Markdown files in data/adventures/.
    """
    ADVENTURES_DIR.mkdir(parents=True, exist_ok=True)
    summary = {"downloaded": 0, "skipped": 0, "failed": 0}

    print(f"\n[ADVENTURES] Memeriksa halaman dan kategori petualangan MouseHunt...")

    # Collect targets: Start with the master page "Adventure Book"
    target_titles: List[str] = [ADVENTURE_BOOK_PAGE]

    # Fetch all pages in Category:Adventures if available
    try:
        cat_members = client.get_category_members(ADVENTURES_CATEGORY, cmtype="page")
        for member in cat_members:
            title = member.get("title")
            if title and title not in target_titles:
                target_titles.append(title)
    except Exception as e:
        print(f"[Warning] Gagal mengambil kategori {ADVENTURES_CATEGORY}: {e}")

    if limit is not None and limit > 0:
        target_titles = target_titles[:limit]

    print(f"[ADVENTURES] Mulai scraping {len(target_titles)} halaman petualangan...")
    pbar = tqdm(target_titles, desc="Adventures", unit="page")

    for title in pbar:
        filename = sanitize_filename(title)
        filepath = ADVENTURES_DIR / filename

        if not force and filepath.exists() and filepath.stat().st_size > 50:
            summary["skipped"] += 1
            pbar.set_postfix({"skip": summary["skipped"], "done": summary["downloaded"]})
            continue

        page_data = client.get_page_data(title)
        if not page_data:
            summary["failed"] += 1
            continue

        entity_type = "adventure_book" if title == ADVENTURE_BOOK_PAGE else "adventure"
        md_content = parse_page_to_rag_markdown(
            parse_data=page_data,
            entity_type=entity_type,
            main_category="Adventures"
        )

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(md_content)
            summary["downloaded"] += 1
        except Exception as e:
            print(f"[Error] Gagal menulis {filepath}: {e}")
            summary["failed"] += 1

        pbar.set_postfix({"done": summary["downloaded"], "skip": summary["skipped"]})

    print(f"\n[ADVENTURES SELESAI] Download: {summary['downloaded']}, Dilewati: {summary['skipped']}, Gagal: {summary['failed']}")
    return summary
