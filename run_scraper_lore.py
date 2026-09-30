import argparse
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from tqdm import tqdm

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Fix Windows console utf-8 encoding
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


from scraper.config import (
    DATA_DIR, LOCATIONS_DIR, ITEMS_DIR, MICE_DIR, MECHANICS_DIR, DEFAULT_DELAY
)
from scraper.api_client import WikiClient
from scraper.parser import sanitize_filename
from scraper.lore_extractor import (
    parse_wiki_page_for_lore,
    extract_mouse_lore_from_file,
    extract_equipment_lore_from_file,
    extract_location_lore_from_file,
    extract_mechanic_lore_from_file,
    replace_em_dashes
)

# Lore Base and Subdirectories
LORE_DIR = PROJECT_ROOT / "lore"
DIR_A = LORE_DIR / "A_plankrun_journal"
DIR_B = LORE_DIR / "B_mice_lore"
DIR_C = LORE_DIR / "C_equipment_lore"
DIR_D = LORE_DIR / "D_world_regions"
DIR_E = LORE_DIR / "E_key_characters"
DIR_F = LORE_DIR / "F_world_mechanics"
DIR_G = LORE_DIR / "G_adventure_book"

PLANKRUN_PAGES = [
    "Torn Pages of Plankrun's Journal",
    "Plankrun",
    "Plankrun's Notes"
]

KEY_CHARACTERS = [
    "King",
    "Larry the Friendly Knight",
    "Ronza",
    "Zugzwang",
    "Plankrun",
    "Cartographer",
    "Trapsmith",
    "Cheese Shoppe",
    "General Store",
    "Charm Shoppe"
]


LEGENDARY_ENTITIES = [
    "Acolyte Mouse",
    "Absolute Acolyte Mouse",
    "Ful'Mina the Mountain Queen",
    "Kalor'ignis of the Geyser",
    "Warmonger Mouse",
    "Mythweaver",
    "Dojo Sensei",
    "Balack the Banished",
    "Eclipse Mouse",
    "Ascended Elder Mouse",
    "Retired Minotaur Mouse",
    "Heart of the Meteor",
    "Deep Mouse",
    "Icewing",
    "Silth Mouse",
    "Dragon Mouse"
]

FACTION_GROUPS = [
    "The Marching Flame",
    "The Forgotten Mice",
    "The Shadow Clan",
    "Indigenous Mice",
    "Followers of Furoma",
    "Balack's Banished",
    "Tribal Isles",
    "Folklore Forest"
]

def print_banner():
    banner = r"""
===================================================================
   📜 MOUSEHUNT LORE SCRAPER & FANFICTION CORPUS GENERATOR 🏰
   Target Folders : lore/A_plankrun_journal ... lore/G_adventure_book
   Purpose        : Basis Pengetahuan AI Naratif & Akurasi Lore
===================================================================
"""
    print(banner)

def split_plankrun_journal_sections(full_md: str, target_dir: Path) -> int:
    """Splits Torn Pages of Plankrun's Journal into individual page files for each section."""
    sections = re.split(r'\n###\s+', full_md)
    if len(sections) <= 1:
        return 0
    count = 0
    for sec in sections[1:]:
        lines = sec.split('\n', 1)
        sub_title = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""
        if not body or len(body) < 10:
            continue
        fname = sanitize_filename(f"Plankrun Page - {sub_title}")
        sub_path = target_dir / fname
        frontmatter = {
            "title": f"Plankrun's Journal: {sub_title}",
            "component": "A_plankrun_journal",
            "section": sub_title
        }
        content = [
            "---",
            yaml.dump(frontmatter, sort_keys=False, allow_unicode=True).strip(),
            "---\n",
            f"# 📜 Plankrun's Journal: {sub_title}\n",
            f"> **Author**: Sir Plankrun (The First MouseHunter)\n",
            f"> **Entry**: {sub_title}\n\n",
            body
        ]
        try:
            with open(sub_path, "w", encoding="utf-8") as f:
                f.write("\n".join(content))
            count += 1
        except Exception:
            pass
    return count

def process_component_a(client: WikiClient, source: str, limit: Optional[int], force: bool) -> Dict[str, int]:
    """Component A: Torn Pages of Plankrun's Journal."""
    DIR_A.mkdir(parents=True, exist_ok=True)
    summary = {"downloaded": 0, "skipped": 0, "failed": 0}
    print("\n[A] Memproses Komponen A: Jurnal & Catatan Plankrun...")

    pages_to_fetch = list(PLANKRUN_PAGES)

    # If online/hybrid, also try querying category
    if source in ["online", "hybrid"]:
        try:
            cat_members = client.get_category_members("Torn Pages of Plankrun's Journal", cmtype="page")
            for m in cat_members:
                t = m.get("title")
                if t and t not in pages_to_fetch:
                    pages_to_fetch.append(t)
        except Exception:
            pass

    if limit is not None:
        pages_to_fetch = pages_to_fetch[:limit]

    pbar = tqdm(pages_to_fetch, desc="[A] Plankrun", unit="page")
    for title in pbar:
        fname = sanitize_filename(title)
        out_path = DIR_A / fname

        if not force and out_path.exists() and out_path.stat().st_size > 50:
            summary["skipped"] += 1
            continue

        if source in ["online", "hybrid"]:
            page_data = client.get_page_data(title)
            if page_data:
                md_content = parse_wiki_page_for_lore(page_data, entity_type="plankrun_journal", component_code="A_plankrun_journal")
                try:
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(md_content)
                    summary["downloaded"] += 1

                    # If Torn Pages, also extract individual section files
                    if "Torn Pages" in title:
                        sub_count = split_plankrun_journal_sections(md_content, DIR_A)
                        if sub_count > 0:
                            summary["downloaded"] += sub_count
                    continue
                except Exception as e:
                    print(f"[Error] Gagal menulis {out_path}: {e}")
                    summary["failed"] += 1
                    continue

        summary["failed"] += 1

    return summary


def process_component_b(client: WikiClient, source: str, limit: Optional[int], force: bool) -> Dict[str, int]:
    """Component B: Mouse Personality, Lore, and Factions."""
    DIR_B.mkdir(parents=True, exist_ok=True)
    summary = {"downloaded": 0, "skipped": 0, "failed": 0}
    print("\n[B] Memproses Komponen B: Lore & Persona Tikus (Mice Lore)...")

    # Local mode check
    local_files = []
    if source in ["hybrid", "local"] and MICE_DIR.exists():
        local_files = sorted(list(MICE_DIR.glob("*.md")), key=lambda p: p.stem.lower())
        # Filter out master index if any
        local_files = [f for f in local_files if f.stem.lower() != "mice"]

    if local_files:
        if limit is not None:
            local_files = local_files[:limit]
        pbar = tqdm(local_files, desc="[B] Mice (Local)", unit="mouse")
        for f in pbar:
            out_path = DIR_B / f.name
            if not force and out_path.exists() and out_path.stat().st_size > 50:
                summary["skipped"] += 1
                continue

            lore_md = extract_mouse_lore_from_file(f)
            if lore_md:
                try:
                    with open(out_path, "w", encoding="utf-8") as out:
                        out.write(lore_md)
                    summary["downloaded"] += 1
                except Exception as e:
                    print(f"[Error] Gagal menulis {out_path}: {e}")
                    summary["failed"] += 1
            else:
                summary["failed"] += 1
        return summary

    # Online fallback
    if source in ["online", "hybrid"]:
        members = client.get_category_members("Mice", cmtype="page", limit=limit)
        pbar = tqdm(members, desc="[B] Mice (Online)", unit="mouse")
        for member in pbar:
            title = member["title"]
            fname = sanitize_filename(title)
            out_path = DIR_B / fname

            if not force and out_path.exists() and out_path.stat().st_size > 50:
                summary["skipped"] += 1
                continue

            page_data = client.get_page_data(title)
            if page_data:
                md_content = parse_wiki_page_for_lore(page_data, entity_type="mouse_lore", component_code="B_mice_lore")
                try:
                    with open(out_path, "w", encoding="utf-8") as out:
                        out.write(md_content)
                    summary["downloaded"] += 1
                except Exception as e:
                    summary["failed"] += 1
            else:
                summary["failed"] += 1

    return summary

def process_component_c(client: WikiClient, source: str, limit: Optional[int], force: bool) -> Dict[str, int]:
    """Component C: Equipment Lore (Weapons & Bases & Crafting)."""
    DIR_C.mkdir(parents=True, exist_ok=True)
    summary = {"downloaded": 0, "skipped": 0, "failed": 0}
    print("\n[C] Memproses Komponen C: Lore Senjata, Base & Rekayasa Perangkap...")

    w_files = []
    b_files = []
    if source in ["hybrid", "local"]:
        w_dir = ITEMS_DIR / "weapons"
        if w_dir.exists():
            w_files = sorted(list(w_dir.glob("*.md")), key=lambda p: p.stem.lower())
        b_dir = ITEMS_DIR / "bases"
        if b_dir.exists():
            b_files = sorted(list(b_dir.glob("*.md")), key=lambda p: p.stem.lower())

    if w_files or b_files:
        items = []
        for wf in w_files:
            items.append((wf, "weapon"))
        for bf in b_files:
            items.append((bf, "base"))

        if limit is not None:
            items = items[:limit]

        pbar = tqdm(items, desc="[C] Equipment", unit="item")
        for file_path, eq_type in pbar:
            prefix = "Weapon - " if eq_type == "weapon" else "Base - "
            fname = sanitize_filename(prefix + file_path.stem)
            out_path = DIR_C / fname

            if not force and out_path.exists() and out_path.stat().st_size > 50:
                summary["skipped"] += 1
                continue

            lore_md = extract_equipment_lore_from_file(file_path, eq_type)
            if lore_md:
                try:
                    with open(out_path, "w", encoding="utf-8") as out:
                        out.write(lore_md)
                    summary["downloaded"] += 1
                except Exception as e:
                    summary["failed"] += 1
            else:
                summary["failed"] += 1
        return summary

    return summary

def process_component_d(client: WikiClient, source: str, limit: Optional[int], force: bool) -> Dict[str, int]:
    """Component D: World Regions and Locations."""
    DIR_D.mkdir(parents=True, exist_ok=True)
    summary = {"downloaded": 0, "skipped": 0, "failed": 0}
    print("\n[D] Memproses Komponen D: Worldbuilding, Region & Wilayah Perburuan...")

    loc_files = []
    if source in ["hybrid", "local"] and LOCATIONS_DIR.exists():
        loc_files = sorted(list(LOCATIONS_DIR.glob("*.md")), key=lambda p: p.stem.lower())

    if loc_files:
        if limit is not None:
            loc_files = loc_files[:limit]
        pbar = tqdm(loc_files, desc="[D] Locations", unit="loc")
        for f in pbar:
            out_path = DIR_D / f.name
            if not force and out_path.exists() and out_path.stat().st_size > 50:
                summary["skipped"] += 1
                continue

            lore_md = extract_location_lore_from_file(f)
            if lore_md:
                try:
                    with open(out_path, "w", encoding="utf-8") as out:
                        out.write(lore_md)
                    summary["downloaded"] += 1
                except Exception:
                    summary["failed"] += 1
            else:
                summary["failed"] += 1
        return summary

    return summary

def process_component_e(client: WikiClient, source: str, limit: Optional[int], force: bool) -> Dict[str, int]:
    """Component E: Key Characters, NPCs, Bosses, and Factions."""
    DIR_E.mkdir(parents=True, exist_ok=True)
    summary = {"downloaded": 0, "skipped": 0, "failed": 0}
    print("\n[E] Memproses Komponen E: Profil Karakter, Tokoh Kunci & Faksi...")

    all_characters = list(KEY_CHARACTERS) + list(LEGENDARY_ENTITIES)
    if limit is not None:
        all_characters = all_characters[:limit]

    pbar = tqdm(all_characters, desc="[E] Characters", unit="char")
    for title in pbar:
        fname = sanitize_filename(title)
        out_path = DIR_E / fname

        if not force and out_path.exists() and out_path.stat().st_size > 50:
            summary["skipped"] += 1
            continue

        # Check if local mouse file exists first for legendary entities
        local_mouse = MICE_DIR / f"{title}.md"
        if local_mouse.exists():
            lore_md = extract_mouse_lore_from_file(local_mouse)
            if lore_md:
                try:
                    with open(out_path, "w", encoding="utf-8") as out:
                        out.write(lore_md)
                    summary["downloaded"] += 1
                    continue
                except Exception:
                    pass

        # Online fetch for NPCs like Larry, The King, Ronza, etc.
        if source in ["online", "hybrid"]:
            page_data = client.get_page_data(title)
            if page_data:
                md_content = parse_wiki_page_for_lore(page_data, entity_type="character", component_code="E_key_characters")
                try:
                    with open(out_path, "w", encoding="utf-8") as out:
                        out.write(md_content)
                    summary["downloaded"] += 1
                    continue
                except Exception:
                    summary["failed"] += 1
            else:
                summary["failed"] += 1

    return summary

def process_component_f(client: WikiClient, source: str, limit: Optional[int], force: bool) -> Dict[str, int]:
    """Component F: World Mechanics, Horn, Ranks, Power Types, Cheese lore."""
    DIR_F.mkdir(parents=True, exist_ok=True)
    summary = {"downloaded": 0, "skipped": 0, "failed": 0}
    print("\n[F] Memproses Komponen F: Hukum Alam, Pangkat, Horn & Elemen...")

    mech_files = []
    if source in ["hybrid", "local"] and MECHANICS_DIR.exists():
        mech_files = sorted(list(MECHANICS_DIR.glob("*.md")), key=lambda p: p.stem.lower())

    if mech_files:
        if limit is not None:
            mech_files = mech_files[:limit]
        pbar = tqdm(mech_files, desc="[F] Mechanics", unit="topic")
        for f in pbar:
            out_path = DIR_F / f.name
            if not force and out_path.exists() and out_path.stat().st_size > 50:
                summary["skipped"] += 1
                continue

            lore_md = extract_mechanic_lore_from_file(f)
            if lore_md:
                try:
                    with open(out_path, "w", encoding="utf-8") as out:
                        out.write(lore_md)
                    summary["downloaded"] += 1
                except Exception:
                    summary["failed"] += 1
            else:
                summary["failed"] += 1
        return summary

    return summary

def process_component_g(client: WikiClient, source: str, limit: Optional[int], force: bool) -> Dict[str, int]:
    """Component G: Adventure Book, Quests & Story Arcs."""
    DIR_G.mkdir(parents=True, exist_ok=True)
    summary = {"downloaded": 0, "skipped": 0, "failed": 0}
    print("\n[G] Memproses Komponen G: Cerita & Alur Petualangan (Adventure Book)...")

    # Local mode check
    local_files = []
    adventures_data_dir = DATA_DIR / "adventures"
    if source in ["hybrid", "local"] and adventures_data_dir.exists():
        local_files = sorted(list(adventures_data_dir.glob("*.md")), key=lambda p: p.stem.lower())

    if local_files:
        if limit is not None:
            local_files = local_files[:limit]
        pbar = tqdm(local_files, desc="[G] Adventures (Local)", unit="adv")
        for f in pbar:
            out_path = DIR_G / f.name
            if not force and out_path.exists() and out_path.stat().st_size > 50:
                summary["skipped"] += 1
                continue

            try:
                with open(f, "r", encoding="utf-8") as inf:
                    c = inf.read()
                c = replace_em_dashes(c)
                with open(out_path, "w", encoding="utf-8") as out:
                    out.write(c)
                summary["downloaded"] += 1
            except Exception as e:
                print(f"[Error] Gagal menulis {out_path}: {e}")
                summary["failed"] += 1
        return summary

    # Online fallback
    if source in ["online", "hybrid"]:
        targets = ["Adventure Book"]
        try:
            cat_members = client.get_category_members("Adventures", cmtype="page")
            for m in cat_members:
                t = m.get("title")
                if t and t not in targets:
                    targets.append(t)
        except Exception:
            pass

        if limit is not None:
            targets = targets[:limit]

        pbar = tqdm(targets, desc="[G] Adventures (Online)", unit="adv")
        for title in pbar:
            fname = sanitize_filename(title)
            out_path = DIR_G / fname

            if not force and out_path.exists() and out_path.stat().st_size > 50:
                summary["skipped"] += 1
                continue

            page_data = client.get_page_data(title)
            if page_data:
                md_content = parse_wiki_page_for_lore(page_data, entity_type="adventure_lore", component_code="G_adventure_book")
                try:
                    with open(out_path, "w", encoding="utf-8") as out:
                        out.write(md_content)
                    summary["downloaded"] += 1
                except Exception:
                    summary["failed"] += 1
            else:
                summary["failed"] += 1

    return summary

def main():
    print_banner()

    parser = argparse.ArgumentParser(
        description="Scraper & Ekstraktor Lore MouseHunt untuk Penulisan Cerita / Fanfiksi AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh Penggunaan:
  1. Eksekusi Penuh (Semua Komponen A sampai G):
     python run_scraper_lore.py --mode all


  2. Eksekusi Komponen Tertentu:
     python run_scraper_lore.py --mode A       # Jurnal Plankrun
     python run_scraper_lore.py --mode B       # Lore Tikus & Faksi
     python run_scraper_lore.py --mode C       # Senjata & Base
     python run_scraper_lore.py --mode D       # Lokasi & Wilayah
     python run_scraper_lore.py --mode E       # Tokoh Kunci & Boss
     python run_scraper_lore.py --mode F       # Aturan Dunia & Mekanik
     python run_scraper_lore.py --mode G       # Kisah Petualangan (Adventure Book)

  3. Uji Coba Cepat (Limit per kategori):
     python run_scraper_lore.py --mode all --limit 10

  4. Paksa Overwrite File yang Ada:
     python run_scraper_lore.py --mode all --force
"""
    )

    parser.add_argument(
        "--mode",
        choices=["all", "A", "B", "C", "D", "E", "F", "G", "plankrun", "mice", "equipment", "regions", "characters", "mechanics", "adventures"],
        default="all",
        help="Komponen lore yang ingin diproses (default: all)."
    )
    parser.add_argument(
        "--source",
        choices=["hybrid", "local", "online"],
        default="hybrid",
        help="Sumber data: 'hybrid' (prioritaskan data lokal yang sudah ada, ambil online jika belum ada), 'local' (lokal saja), 'online' (unduh segar dari wiki)."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Batas jumlah item per komponen untuk pengujian cepat."
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY,
        help=f"Jeda waktu antar request API dalam detik (default: {DEFAULT_DELAY}s)."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Timpa (overwrite) file lore yang sudah ada di direktori tujuan."
    )

    args = parser.parse_args()

    client = WikiClient(delay=args.delay)
    start_time = time.time()

    print(f"[*] Target Folder Utama : {LORE_DIR}")
    print(f"[*] Mode Komponen       : {args.mode.upper()}")
    print(f"[*] Sumber Data         : {args.source.upper()}")
    print(f"[*] Force Overwrite     : {'YA' if args.force else 'TIDAK (Skip yang sudah ada)'}\n")

    LORE_DIR.mkdir(parents=True, exist_ok=True)

    summaries = {}

    run_all = (args.mode == "all")

    if run_all or args.mode in ["A", "plankrun"]:
        summaries["A_plankrun_journal"] = process_component_a(client, args.source, args.limit, args.force)

    if run_all or args.mode in ["B", "mice"]:
        summaries["B_mice_lore"] = process_component_b(client, args.source, args.limit, args.force)

    if run_all or args.mode in ["C", "equipment"]:
        summaries["C_equipment_lore"] = process_component_c(client, args.source, args.limit, args.force)

    if run_all or args.mode in ["D", "regions"]:
        summaries["D_world_regions"] = process_component_d(client, args.source, args.limit, args.force)

    if run_all or args.mode in ["E", "characters"]:
        summaries["E_key_characters"] = process_component_e(client, args.source, args.limit, args.force)

    if run_all or args.mode in ["F", "mechanics"]:
        summaries["F_world_mechanics"] = process_component_f(client, args.source, args.limit, args.force)

    if run_all or args.mode in ["G", "adventures"]:
        summaries["G_adventure_book"] = process_component_g(client, args.source, args.limit, args.force)


    elapsed = time.time() - start_time
    total_dl = sum(s["downloaded"] for s in summaries.values())
    total_skip = sum(s["skipped"] for s in summaries.values())
    total_fail = sum(s["failed"] for s in summaries.values())

    print("\n" + "=" * 65)
    print("             RINGKASAN SCRAPING & EKSTRAKSI LORE")
    print("=" * 65)
    for comp, stats in summaries.items():
        print(f"  • {comp:<22} : {stats['downloaded']} dibuat, {stats['skipped']} dilewati, {stats['failed']} gagal")
    print("-" * 65)
    print(f"  Total File Baru/Terisi    : {total_dl}")
    print(f"  Total File Dilewati       : {total_skip}")
    print(f"  Total File Gagal/Kosong   : {total_fail}")
    print(f"  Waktu Eksekusi            : {elapsed:.2f} detik")
    print(f"  Folder Hasil              : {LORE_DIR}")
    print("=" * 65)
    print("Selesai! Sekarang Anda dapat menjalankan 'python bundle.py' untuk membuat bundel master cerita. 🚀\n")

if __name__ == "__main__":
    main()
