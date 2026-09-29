import os
import re
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Dict, Any, Set, Optional
import yaml
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parent

# Fix Windows console utf-8 encoding
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

LORE_DIR = PROJECT_ROOT / "lore"
BUNDLES_DIR = PROJECT_ROOT / "bundles_lore"


def replace_em_dashes(text: str) -> str:
    """Ensure no em-dashes exist in bundle content."""
    if not text:
        return ""
    return text.replace("—", "-").replace("–", "-")

def extract_metadata_and_body(content: str) -> Tuple[Dict[str, Any], str]:
    """Extract YAML frontmatter and body text from a markdown file."""
    metadata = {}
    body = content
    content = replace_em_dashes(content)

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                metadata = yaml.safe_load(parts[1]) or {}
            except Exception:
                metadata = {}
            body = parts[2].strip()

    return metadata, body

def clean_markdown_body(body: str) -> str:
    """Normalize whitespace and remove excessive blank lines."""
    body = re.sub(r'\n{3,}', '\n\n', body)
    return body.strip()

def build_lore_section(file_path: Path, icon: str, default_type: str) -> Tuple[str, str]:
    """
    Formats an individual lore markdown file into a clean, separated section within a master bundle.
    Returns: (title, section_markdown)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_content = f.read()
    except Exception as e:
        print(f"[Warning] Gagal membaca {file_path.name}: {e}")
        return "", ""

    metadata, body = extract_metadata_and_body(raw_content)
    title = metadata.get("title", file_path.stem)
    entity_type = metadata.get("type", default_type)

    cleaned_body = clean_markdown_body(body)
    # Remove redundant title heading if already present (with or without icon)
    cleaned_body = re.sub(r"^#\s+[^\n]+\n*", "", cleaned_body).strip()


    meta_parts = [f"**Entity**: {entity_type.capitalize()}"]
    if "faction_group" in metadata:
        meta_parts.append(f"**Faction**: {metadata['faction_group']}")
    if "region" in metadata:
        meta_parts.append(f"**Region**: {metadata['region']}")
    if "power_type" in metadata:
        meta_parts.append(f"**Element**: {metadata['power_type']}")
    if "rank_required" in metadata:
        meta_parts.append(f"**Rank**: {metadata['rank_required']}")

    meta_bar = " | ".join(meta_parts)

    section = [
        f"# {icon} {title}\n",
        f"> {meta_bar}\n",
        cleaned_body,
        "\n\n---\n"
    ]
    return title, "\n".join(section)

DEFAULT_MICE_GROUPS = [
    ("part1_A-C", "A - C", set("ABC")),
    ("part2_D-H", "D - H", set("DEFGH")),
    ("part3_I-M", "I - M", set("IJKLM")),
    ("part4_N-R", "N - R", set("NOPQR")),
    ("part5_S", "S", set("S")),
    ("part6_T-Z", "T - Z", set("TUVWXYZ")),
]

def bundle_component(
    component_folder: Path,
    output_filename: str,
    bundle_title: str,
    bundle_desc: str,
    icon: str,
    default_type: str,
    output_dir: Optional[Path] = None
) -> Optional[Tuple[Path, int, int]]:
    """Bundles all markdown files in a component folder into a single master markdown file."""
    if not component_folder.exists():
        return None

    files = sorted(list(component_folder.glob("*.md")), key=lambda p: p.stem.lower())
    if not files:
        return None

    target_dir = output_dir or BUNDLES_DIR
    output_file = target_dir / output_filename
    print(f"\n[*] Menggabungkan {len(files)} file dari {component_folder.name} ke {output_file.name}...")

    seen_titles: Set[str] = set()
    entity_sections = []

    for file_path in tqdm(files, desc=bundle_title[:30], unit="file"):
        title, sec = build_lore_section(file_path, icon, default_type)
        if not title or title in seen_titles:
            continue
        seen_titles.add(title)
        entity_sections.append(sec)

    sections = [
        f"# {bundle_title}\n",
        f"{bundle_desc}\n",
        f"**Total Entitas**: {len(seen_titles)} entitas cerita  \n",
        "## 📑 Daftar Isi / Index:\n"
    ]

    for title in sorted(seen_titles):
        sections.append(f"- {title}")

    sections.append("\n---\n")
    sections.extend(entity_sections)

    content = "\n".join(sections)
    content = replace_em_dashes(content)

    with open(output_file, "w", encoding="utf-8") as out:
        out.write(content)

    return output_file, len(seen_titles), len(content)

def _write_mice_bundle_file(
    files: List[Path],
    output_file: Path,
    title: str,
    desc: str,
    icon: str,
    default_type: str
) -> Optional[Tuple[Path, int, int]]:
    """Writes a single partition of mice lore into a markdown bundle."""
    if not files:
        return None

    print(f"\n[*] Menggabungkan {len(files)} file tikus ke {output_file.name}...")

    seen_titles: Set[str] = set()
    entity_sections = []

    for file_path in tqdm(files, desc=title[:30], unit="file"):
        t, sec = build_lore_section(file_path, icon, default_type)
        if not t or t in seen_titles:
            continue
        seen_titles.add(t)
        entity_sections.append(sec)

    sections = [
        f"# {title}\n",
        f"{desc}\n",
        f"**Total Entitas**: {len(seen_titles)} entitas tikus  \n",
        "## 📑 Daftar Isi / Index:\n"
    ]

    for t in sorted(seen_titles, key=lambda s: re.sub(r"^[^a-zA-Z0-9]+", "", s).lower()):
        sections.append(f"- {t}")

    sections.append("\n---\n")
    sections.extend(entity_sections)

    content = "\n".join(sections)
    content = replace_em_dashes(content)

    with open(output_file, "w", encoding="utf-8") as out:
        out.write(content)

    return output_file, len(seen_titles), len(content)

def bundle_mice_split(
    component_folder: Path,
    output_dir: Path,
    base_title: str = "Bestiari & Ensiklopedia Lore Tikus",
    base_desc: str = "Kompilasi lengkap deskripsi cerita, kepribadian, faksi, habitat, kelemahan elemen, dan kebiasaan umpan spesies tikus Kerajaan Gnawnia.",
    icon: str = "🐭",
    default_type: str = "Mouse",
    chunk_size: Optional[int] = None
) -> List[Tuple[Path, int, int]]:
    """
    Bundles mice markdown files into multiple smaller markdown files to prevent oversized bundles.
    Supports alphabetical letter ranges (default: 6 balanced parts) or fixed entity chunk size.
    """
    if not component_folder.exists():
        return []

    # Clean old monolithic file if exists
    old_monolithic = output_dir / "02_mice_bestiary_lore.md"
    if old_monolithic.exists():
        try:
            old_monolithic.unlink()
            print(f"[Info] Menghapus bundel lama yang terlalu besar: {old_monolithic.name}")
        except Exception as e:
            print(f"[Warning] Gagal menghapus {old_monolithic.name}: {e}")

    def sort_key(p: Path) -> str:
        clean = re.sub(r"^[^a-zA-Z0-9]+", "", p.stem).lower()
        return clean or p.stem.lower()

    files = sorted(list(component_folder.glob("*.md")), key=sort_key)
    if not files:
        return []

    results = []

    if chunk_size and chunk_size > 0:
        file_batches = [files[i:i + chunk_size] for i in range(0, len(files), chunk_size)]
        for idx, batch in enumerate(file_batches, start=1):
            first_name = re.sub(r"^[^a-zA-Z0-9]+", "", batch[0].stem)
            last_name = re.sub(r"^[^a-zA-Z0-9]+", "", batch[-1].stem)
            first_letter = first_name[0].upper() if first_name else "A"
            last_letter = last_name[0].upper() if last_name else "Z"

            part_suffix = f"part{idx}_{first_letter}-{last_letter}"
            part_label = f"Bagian {idx}: {first_letter} - {last_letter}"
            output_filename = f"02_mice_bestiary_{part_suffix}.md"

            res = _write_mice_bundle_file(
                files=batch,
                output_file=output_dir / output_filename,
                title=f"{icon} {base_title} ({part_label})",
                desc=f"{base_desc} (Abjad {first_letter} - {last_letter})",
                icon=icon,
                default_type=default_type
            )
            if res:
                results.append(res)
    else:
        grouped_files: Dict[str, List[Path]] = {g[0]: [] for g in DEFAULT_MICE_GROUPS}

        for p in files:
            clean = re.sub(r"^[^a-zA-Z0-9]+", "", p.stem).upper()
            first_char = clean[0] if clean else "A"
            assigned = False
            for group_id, _, letters in DEFAULT_MICE_GROUPS:
                if first_char in letters:
                    grouped_files[group_id].append(p)
                    assigned = True
                    break
            if not assigned:
                grouped_files["part6_T-Z"].append(p)

        for idx, (group_id, letter_range, _) in enumerate(DEFAULT_MICE_GROUPS, start=1):
            batch = grouped_files.get(group_id, [])
            if not batch:
                continue
            part_label = f"Bagian {idx}: {letter_range}"
            output_filename = f"02_mice_bestiary_{group_id}.md"

            res = _write_mice_bundle_file(
                files=batch,
                output_file=output_dir / output_filename,
                title=f"{icon} {base_title} ({part_label})",
                desc=f"{base_desc} (Abjad {letter_range})",
                icon=icon,
                default_type=default_type
            )
            if res:
                results.append(res)

    return results

def bundle_all_in_one(bundles: List[Tuple[Path, int, int]], output_dir: Optional[Path] = None) -> Optional[Path]:
    """Compiles all individual lore bundles into one single Master Lore Bible."""
    target_dir = output_dir or BUNDLES_DIR
    bible_file = target_dir / "00_mousehunt_lore_bible.md"
    print(f"\n[*] Mengompilasi Master Lore Bible: {bible_file.name}...")

    bible_parts = [
        "# 📖 MOUSEHUNT UNIVERSE: THE COMPLETE LORE BIBLE\n",
        "> Kompendium lengkap dunia Kerajaan Gnawnia untuk AI Agent Penulis Cerita dan Fanfiksi.",
        "> Berisi catatan sejarah Plankrun, bestiari seluruh spesies tikus, rekayasa senjata, geografi wilayah, profil tokoh, dan hukum alam perburuan.\n",
        "---\n"
    ]

    for bundle_path, count, _ in bundles:
        try:
            with open(bundle_path, "r", encoding="utf-8") as f:
                c = f.read()
            bible_parts.append(c)
            bible_parts.append("\n\n---\n\n")
        except Exception:
            pass

    full_bible = "\n".join(bible_parts)
    full_bible = replace_em_dashes(full_bible)

    with open(bible_file, "w", encoding="utf-8") as out:
        out.write(full_bible)

    return bible_file

def main():
    parser = argparse.ArgumentParser(
        description="Bundler Lore MouseHunt: Menggabungkan file komponen lore menjadi bundel master Markdown untuk RAG / LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh Penggunaan:
  1. Bundel semua komponen lore (tikus dipecah otomatis menjadi beberapa bagian):
     python bundle.py

  2. Bundel tikus saja:
     python bundle.py --component B

  3. Bundel tikus dengan pembagian per jumlah entitas (misal 200 per file):
     python bundle.py --component B --mice-chunk-size 200

  4. Bundel tikus menjadi satu file utuh monolithic (format lama):
     python bundle.py --component B --mice-monolithic

  5. Bundel semua komponen sekaligus buat satu file Master Lore Bible:
     python bundle.py --all-in-one
"""
    )

    parser.add_argument(
        "--lore-dir",
        type=str,
        default=str(LORE_DIR),
        help=f"Direktori data lore masukan (default: {LORE_DIR})."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(BUNDLES_DIR),
        help=f"Direktori penyimpanan bundel (default: {BUNDLES_DIR})."
    )
    parser.add_argument(
        "--component",
        choices=["all", "A", "B", "C", "D", "E", "F"],
        default="all",
        help="Komponen lore yang ingin dibundel (default: all)."
    )
    parser.add_argument(
        "--mice-chunk-size",
        type=int,
        default=None,
        help="Ukuran pembagian tikus per file berdasarkan jumlah entitas (misal: 250). Default: pembagian abjad alami (6 bagian)."
    )
    parser.add_argument(
        "--mice-monolithic",
        action="store_true",
        help="Buat satu file bundel tikus utuh (02_mice_bestiary_lore.md) tanpa dipecah."
    )
    parser.add_argument(
        "--all-in-one",
        action="store_true",
        help="Buat juga satu file master kompendium utuh (00_mousehunt_lore_bible.md)."
    )

    args = parser.parse_args()

    input_lore = Path(args.lore_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("      📜 MOUSEHUNT LORE BUNDLER (FANFICTION MASTER CORPUS)    ")
    print("=" * 65)
    print(f"Direktori Lore Masukan : {input_lore}")
    print(f"Direktori Output Bundel: {out_dir}\n")

    components_config = [
        (
            "A",
            input_lore / "A_plankrun_journal",
            "01_plankrun_chronicles.md",
            "📜 Kronik & Jurnal Ekspedisi Plankrun (The First Hunter)",
            "Kumpulan lengkap catatan harian, potongan jurnal (torn pages), dan observasi lapangan Plankrun sang pemburu pertama.",
            "📜",
            "Journal"
        ),
        (
            "B",
            input_lore / "B_mice_lore",
            "02_mice_bestiary_lore.md",
            "🐭 Bestiari & Ensiklopedia Lore Seluruh Spesies Tikus",
            "Kompilasi lengkap deskripsi cerita, kepribadian, faksi, habitat, kelemahan elemen, dan kebiasaan umpan seluruh spesies tikus Kerajaan Gnawnia.",
            "🐭",
            "Mouse"
        ),
        (
            "C",
            input_lore / "C_equipment_lore",
            "03_equipment_armory_lore.md",
            "⚔️ Gudang Persenjataan & Rekayasa Perangkap (Armory & Bases)",
            "Deskripsi latar belakang teknologi perangkap, perakitan robot Ambush, mesin uap Digby, kristal mistis Arcane, dan base pertahanan.",
            "⚔️",
            "Equipment"
        ),
        (
            "D",
            input_lore / "D_world_regions",
            "04_world_regions_travelogue.md",
            "🗺️ Panduan Wilayah, Geografi & Narasi Lingkungan (Travelogue)",
            "Eksplorasi mendalam atmosfer seluruh wilayah berburu: nuansa pedesaan Gnawnia, kota bawah tanah Digby, kuil Furoma, benteng Fort Rox, hingga dimensi Rift.",
            "📍",
            "Location"
        ),
        (
            "E",
            input_lore / "E_key_characters",
            "05_dramatis_personae_factions.md",
            "👤 Tokoh Kunci, Karakter Legendaris & Faksi Kerajaan (Dramatis Personae)",
            "Profil mendalam tokoh sentral Kerajaan: The King, Larry the Friendly Knight, Ronza si penjelajah udara, penyihir Zugzwang, para Sensei, dan musuh bebuyutan.",
            "👤",
            "Character"
        ),
        (
            "F",
            input_lore / "F_world_mechanics",
            "06_world_laws_and_mechanics.md",
            "⚙️ Hukum Alam, Tradisi Pemburu & Mekanik Cerita (World Rules)",
            "Aturan semesta MouseHunt: gema Terompet Pemburu (Hunter's Horn), hierarki pangkat Novice-Elder, 10 elemen kekuatan perangkap, dan magis aroma keju.",
            "⚙️",
            "Mechanic"
        )
    ]

    results = []

    for code, folder, filename, title, desc, icon, def_type in components_config:
        if args.component != "all" and args.component != code:
            continue

        if code == "B" and not args.mice_monolithic:
            mice_res = bundle_mice_split(
                component_folder=folder,
                output_dir=out_dir,
                base_title="Bestiari & Ensiklopedia Lore Tikus",
                base_desc=desc,
                icon=icon,
                default_type=def_type,
                chunk_size=args.mice_chunk_size
            )
            results.extend(mice_res)
        else:
            res = bundle_component(
                component_folder=folder,
                output_filename=filename,
                bundle_title=title,
                bundle_desc=desc,
                icon=icon,
                default_type=def_type,
                output_dir=out_dir
            )
            if res:
                results.append(res)

    if not results:
        print("\n[!] Belum ada file lore yang ditemukan di folder masukan.")
        print("    Jalankan terlebih dahulu: python run_scraper_lore.py --mode all")
        return

    # Master bible if requested
    bible_res = None
    if args.all_in_one and len(results) > 1:
        bible_res = bundle_all_in_one(results, out_dir)

    print("\n" + "=" * 65)
    print("                 RINGKASAN BUNDEL LORE TERCIPTA")
    print("=" * 65)
    total_bytes = 0
    total_chars = 0
    for out_path, count, char_len in results:
        size_mb = out_path.stat().st_size / (1024 * 1024)
        est_tokens = char_len // 4
        total_bytes += out_path.stat().st_size
        total_chars += char_len
        print(f"  📄 {out_path.name}")
        print(f"     • Entitas Unik   : {count:,} entitas")
        print(f"     • Ukuran File    : {size_mb:.2f} MB")
        print(f"     • Estimasi Token : ~{est_tokens:,} tokens")
        print(f"     • Lokasi File    : {out_path}")
        print("-" * 65)

    if bible_res:
        bible_mb = bible_res.stat().st_size / (1024 * 1024)
        print(f"  🌟 MASTER COMPENDIUM: {bible_res.name} ({bible_mb:.2f} MB)")
        print("-" * 65)

    grand_mb = total_bytes / (1024 * 1024)
    grand_tokens = total_chars // 4
    print(f"  Total Ukuran Seluruh Bundel : {grand_mb:.2f} MB")
    print(f"  Total Estimasi Token        : ~{grand_tokens:,} tokens")
    print("=" * 65)
    print("Bundel siap digunakan sebagai Knowledge Base AI untuk menulis cerita/fanfiksi! 🚀\n")

if __name__ == "__main__":
    main()
