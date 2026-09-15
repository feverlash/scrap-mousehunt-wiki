import argparse
import sys
import time
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scraper.config import (
    DATA_DIR, LOCATIONS_DIR, ITEMS_DIR, MICE_DIR, MECHANICS_DIR,
    PILOT_ITEM_LIMIT, PILOT_MICE_LIMIT, PILOT_LOCATION_LIMIT,
    ITEM_CATEGORIES, DEFAULT_DELAY
)
from scraper.api_client import WikiClient
from scraper.scrape_locations import scrape_all_locations
from scraper.scrape_mechanics import scrape_core_mechanics
from scraper.scrape_items import scrape_all_items
from scraper.scrape_mice import scrape_all_mice

def print_banner():
    banner = r"""
===================================================================
   🐭 MOUSEHUNT WIKI SCRAPER & RAG MARKDOWN GENERATOR 🧀
   Source: https://mhwiki.hitgrab.com/wiki/
   Scope: Locations, Mechanics, Items & Mice (No Trivia/Noise)
===================================================================
"""
    print(banner)

def main():
    print_banner()

    parser = argparse.ArgumentParser(
        description="Scraper MouseHunt Wiki untuk RAG AI (Gameplay, Locations, Items & Mice -> Markdown)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh Penggunaan:
  1. Uji coba sampel (Pilot Run):
     python run_scraper.py --mode pilot --force

  2. Eksekusi Penuh (Full Run - Locations, Mechanics, Items, lalu Mice):
     python run_scraper.py --mode full --force

  3. Scrape Lokasi saja:
     python run_scraper.py --mode locations

  4. Scrape Mekanik & Skin Fungsional saja:
     python run_scraper.py --mode mechanics

  5. Scrape Items saja:
     python run_scraper.py --mode items

  6. Scrape Mice saja:
     python run_scraper.py --mode mice
"""
    )

    parser.add_argument(
        "--mode",
        choices=["pilot", "full", "locations", "mechanics", "items", "mice"],
        default="pilot",
        help="Mode eksekusi: 'pilot', 'full', 'locations', 'mechanics', 'items', 'mice'."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Batas jumlah item per kategori / jumlah tikus / lokasi (opsional)."
    )
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        choices=list(ITEM_CATEGORIES.keys()),
        help="Nama kategori item tertentu (misal: Weapons, Bases, Cheese, Charms)."
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY,
        help=f"Jeda waktu antar-request ke server dalam detik (default: {DEFAULT_DELAY}s)."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Timpa (overwrite) file yang sudah ada di disk."
    )

    args = parser.parse_args()

    client = WikiClient(delay=args.delay)
    start_time = time.time()

    print(f"[*] Mode yang dipilih   : {args.mode.upper()}")
    print(f"[*] Delay per request   : {args.delay} detik")
    print(f"[*] Force overwrite     : {'YA (Menimpa file lama)' if args.force else 'TIDAK (Skip file lama)'}")
    print(f"[*] Direktori Data      : {DATA_DIR}\n")

    loc_summary = {"downloaded": 0, "skipped": 0, "failed": 0}
    mech_summary = {"downloaded": 0, "skipped": 0, "failed": 0}
    item_summary = {"downloaded": 0, "skipped": 0, "failed": 0}
    mice_summary = {"downloaded": 0, "skipped": 0, "failed": 0}

    # MODE: PILOT (Uji Coba Sampel)
    if args.mode == "pilot":
        limit_loc = args.limit if args.limit is not None else PILOT_LOCATION_LIMIT
        limit_items = args.limit if args.limit is not None else PILOT_ITEM_LIMIT
        limit_mice = args.limit if args.limit is not None else PILOT_MICE_LIMIT

        print(f"=== [PILOT 1/4: LOCATIONS] (Maksimal {limit_loc} lokasi) ===")
        loc_summary = scrape_all_locations(client, limit=limit_loc, force=args.force)

        print(f"\n=== [PILOT 2/4: CORE MECHANICS & FUNCTIONAL SKINS] ===")
        mech_summary = scrape_core_mechanics(client, force=args.force)

        print(f"\n=== [PILOT 3/4: ITEMS] (Maksimal {limit_items} per kategori) ===")
        item_summary = scrape_all_items(client, limit_per_category=limit_items, specific_category=args.category, force=args.force)

        print(f"\n=== [PILOT 4/4: MICE] (Maksimal {limit_mice} tikus) ===")
        mice_summary = scrape_all_mice(client, limit=limit_mice, force=args.force)

    # MODE: FULL (Seluruh Data)
    elif args.mode == "full":
        print("=== [TAHAP 1/4: SEMUA LOCATIONS] ===")
        loc_summary = scrape_all_locations(client, limit=args.limit, force=args.force)

        print("\n=== [TAHAP 2/4: CORE MECHANICS & FUNCTIONAL SKINS] ===")
        mech_summary = scrape_core_mechanics(client, force=args.force)

        print("\n=== [TAHAP 3/4: SEMUA ITEMS] ===")
        item_summary = scrape_all_items(client, limit_per_category=args.limit, specific_category=args.category, force=args.force)

        print("\n=== [TAHAP 4/4: SEMUA MICE] ===")
        mice_summary = scrape_all_mice(client, limit=args.limit, force=args.force)

    # MODE: LOCATIONS ONLY
    elif args.mode == "locations":
        print("=== [MODE KHUSUS: LOCATIONS ONLY] ===")
        loc_summary = scrape_all_locations(client, limit=args.limit, force=args.force)

    # MODE: MECHANICS ONLY
    elif args.mode == "mechanics":
        print("=== [MODE KHUSUS: MECHANICS & FUNCTIONAL SKINS ONLY] ===")
        mech_summary = scrape_core_mechanics(client, force=args.force)

    # MODE: ITEMS ONLY
    elif args.mode == "items":
        print("=== [MODE KHUSUS: ITEMS ONLY] ===")
        item_summary = scrape_all_items(client, limit_per_category=args.limit, specific_category=args.category, force=args.force)

    # MODE: MICE ONLY
    elif args.mode == "mice":
        print("=== [MODE KHUSUS: MICE ONLY] ===")
        mice_summary = scrape_all_mice(client, limit=args.limit, force=args.force)

    elapsed = time.time() - start_time
    total_downloaded = loc_summary["downloaded"] + mech_summary["downloaded"] + item_summary["downloaded"] + mice_summary["downloaded"]
    total_skipped = loc_summary["skipped"] + mech_summary["skipped"] + item_summary["skipped"] + mice_summary["skipped"]
    total_failed = loc_summary["failed"] + mech_summary["failed"] + item_summary["failed"] + mice_summary["failed"]

    print("\n" + "=" * 65)
    print("                 RINGKASAN HASIL EKSEKUSI")
    print("=" * 65)
    print(f"  • Total File Baru/Diperbarui : {total_downloaded}")
    print(f"  • File Dilewati (Sudah Ada)  : {total_skipped}")
    print(f"  • Gagal / Error              : {total_failed}")
    print(f"  • Total Waktu Eksekusi       : {elapsed:.2f} detik ({elapsed/60:.2f} menit)")
    print(f"  • Lokasi Output Data         : {DATA_DIR}")
    print("=" * 65)
    print("Korpus siap digunakan untuk RAG AI Anda! 🚀\n")

if __name__ == "__main__":
    main()
