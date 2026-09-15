import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any, Set
import yaml
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
BUNDLES_DIR = PROJECT_ROOT / "bundles"

def extract_metadata_and_body(content: str) -> Tuple[Dict[str, Any], str]:
    """Extract YAML frontmatter and body text from a markdown file."""
    metadata = {}
    body = content

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

def build_entity_section(file_path: Path, icon: str, default_type: str) -> Tuple[str, str]:
    """
    Formats an individual markdown file into a clean, separated section within a bundle.
    Returns: (canonical_title, section_markdown)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_content = f.read()
    except Exception as e:
        print(f"[Warning] Failed to read {file_path.name}: {e}")
        return "", ""

    metadata, body = extract_metadata_and_body(raw_content)
    title = metadata.get("title", metadata.get("name", file_path.stem))
    entity_type = metadata.get("type", default_type)
    category = metadata.get("category", "")
    wiki_url = metadata.get("wiki_url", "")

    cleaned_body = clean_markdown_body(body)
    if cleaned_body.startswith(f"# {title}"):
        lines = cleaned_body.split("\n", 1)
        cleaned_body = lines[1].strip() if len(lines) > 1 else ""

    meta_parts = [f"**Type**: {entity_type.capitalize()}"]
    if category:
        meta_parts.append(f"**Category**: {category}")
    if wiki_url:
        meta_parts.append(f"**Source**: [{title}]({wiki_url})")
    meta_bar = " | ".join(meta_parts)

    section = [
        f"# {icon} {title}\n",
        f"> {meta_bar}\n",
        cleaned_body,
        "\n\n---\n"
    ]
    return title, "\n".join(section)

def bundle_files(
    output_filename: str,
    bundle_title: str,
    bundle_desc: str,
    file_tuples: List[Tuple[Path, str, str]],
    desc_label: str
) -> Tuple[Path, int, int]:
    """Generic helper to bundle files with automatic deduplication of redirected master pages."""
    output_file = BUNDLES_DIR / output_filename
    print(f"\n[*] Menggabungkan {len(file_tuples)} file ke {output_file.name}...")

    seen_titles: Set[str] = set()
    redirected_aliases: Dict[str, str] = {}
    sections = [
        f"# {bundle_title}\n",
        f"{bundle_desc}\n",
        "## 📑 Daftar Isi / Index:\n"
    ]

    entity_sections = []

    for file_path, icon, def_type in tqdm(file_tuples, desc=desc_label, unit="file"):
        canonical_title, sec = build_entity_section(file_path, icon, def_type)
        if not canonical_title:
            continue

        file_label = file_path.stem

        # Deduplication: If the page redirected to a master page (e.g. Crafting Items or Potion),
        # only output the full master page ONCE to prevent 40+ MB of identical repetition!
        if canonical_title in seen_titles:
            if file_label.lower() != canonical_title.lower():
                redirected_aliases[file_label] = canonical_title
            continue

        seen_titles.add(canonical_title)
        entity_sections.append(sec)

    # Build Index in header
    for title in sorted(seen_titles):
        sections.append(f"- {title}")

    if redirected_aliases:
        sections.append("\n### 🔗 Item Tambahan yang Tercakup dalam Tabel Master:")
        for alias, target in sorted(redirected_aliases.items())[:50]:
            sections.append(f"- **{alias}** *(tercantum dalam tabel {target})*")
        if len(redirected_aliases) > 50:
            sections.append(f"- *...dan {len(redirected_aliases) - 50} item lainnya yang tercantum dalam tabel master di atas.*")

    sections.append("\n---\n")
    sections.extend(entity_sections)

    content = "\n".join(sections)
    with open(output_file, "w", encoding="utf-8") as out:
        out.write(content)

    return output_file, len(seen_titles), len(content)

def bundle_locations():
    """Bundle 1: Locations."""
    loc_dir = DATA_DIR / "locations"
    if not loc_dir.exists(): return None
    files = sorted(list(loc_dir.glob("*.md")), key=lambda p: p.stem.lower())
    if not files: return None

    file_tuples = [(f, "📍 Location:", "Location") for f in files]
    return bundle_files(
        output_filename="01_mousehunt_locations.md",
        bundle_title="🗺️ MouseHunt Knowledge Base: Hunting Locations",
        bundle_desc="Ensiklopedia lengkap seluruh wilayah perburuan di MouseHunt: syarat rank, peta travel, inventaris toko, mekanik area/HUD, dan tabel tikus beserta umpan keju.",
        file_tuples=file_tuples,
        desc_label="Bundling Locations"
    )

def bundle_mechanics():
    """Bundle 2: Core Gameplay Mechanics & Progression."""
    mech_dir = DATA_DIR / "mechanics"
    if not mech_dir.exists(): return None
    files = sorted(list(mech_dir.glob("*.md")), key=lambda p: p.stem.lower())
    if not files: return None

    file_tuples = [(f, "⚙️ Topic:", "Mechanic") for f in files]
    return bundle_files(
        output_filename="02_mousehunt_mechanics.md",
        bundle_title="⚙️ MouseHunt Knowledge Base: Core Mechanics & Progression",
        bundle_desc="Panduan lengkap aturan permainan, progresi pangkat (Rank Novice hingga Elder), alur travel & peta Cartographer, efek Auras, panduan Trap Skins dan modul skin fungsional.",
        file_tuples=file_tuples,
        desc_label="Bundling Mechanics"
    )

def bundle_equipment():
    """Bundle 3: Equipment (Weapons & Bases)."""
    items_dir = DATA_DIR / "items"
    if not items_dir.exists(): return None

    file_tuples = []
    # 1. Weapons
    w_dir = items_dir / "weapons"
    if w_dir.exists():
        for f in sorted(list(w_dir.glob("*.md")), key=lambda p: p.stem.lower()):
            file_tuples.append((f, "⚔️ Weapon:", "Weapon"))
    # 2. Bases
    b_dir = items_dir / "bases"
    if b_dir.exists():
        for f in sorted(list(b_dir.glob("*.md")), key=lambda p: p.stem.lower()):
            file_tuples.append((f, "🛡️ Base:", "Base"))

    if not file_tuples: return None

    return bundle_files(
        output_filename="03_mousehunt_equipment.md",
        bundle_title="⚔️ MouseHunt Knowledge Base: Equipment (Weapons & Bases)",
        bundle_desc="Katalog lengkap persenjataan pemburu: Seluruh Senjata/Perangkap (Power, Luck, Power Type, Title Required, Shoppe) dan Seluruh Base perangkap berserta efek khususnya.",
        file_tuples=file_tuples,
        desc_label="Bundling Equipment"
    )

def bundle_consumables():
    """Bundle 4: Consumables (Cheese, Charms, Potions, Special Items, Auras)."""
    items_dir = DATA_DIR / "items"
    if not items_dir.exists(): return None

    file_tuples = []
    cat_map = [
        ("cheese", "🧀 Cheese:", "Cheese"),
        ("charms", "✨ Charm:", "Charm"),
        ("potions", "🧪 Potion:", "Potion"),
        ("special", "📦 Special Item:", "Special"),
        ("auras", "🌟 Aura:", "Aura")
    ]

    for subfolder, icon, def_type in cat_map:
        sub_dir = items_dir / subfolder
        if sub_dir.exists():
            for f in sorted(list(sub_dir.glob("*.md")), key=lambda p: p.stem.lower()):
                file_tuples.append((f, icon, def_type))

    if not file_tuples: return None

    return bundle_files(
        output_filename="04_mousehunt_consumables.md",
        bundle_title="🧀 MouseHunt Knowledge Base: Consumables (Cheese, Charms, Potions & Special)",
        bundle_desc="Katalog lengkap bahan konsumsi berburu: Seluruh Umpan Keju & formula attraction rate, Charms & bonus stats per hunt, Potions konversi keju, dan Special convertible items.",
        file_tuples=file_tuples,
        desc_label="Bundling Consumables"
    )

def bundle_crafting():
    """Bundle 5: Crafting (Ingredients, Blueprints, Parts, Recipes)."""
    items_dir = DATA_DIR / "items"
    c_dir = items_dir / "crafting" if items_dir.exists() else None
    if not c_dir or not c_dir.exists(): return None

    files = sorted(list(c_dir.glob("*.md")), key=lambda p: p.stem.lower())
    if not files: return None

    file_tuples = [(f, "🔨 Crafting:", "Crafting") for f in files]
    return bundle_files(
        output_filename="05_mousehunt_crafting.md",
        bundle_title="🔨 MouseHunt Knowledge Base: Crafting & Blueprints",
        bundle_desc="Direktori lengkap resep perakitan MouseHunt: Blueprint senjata/base, komponen suku cadang, bahan mentah crafting, dan tabel master resep Hunter's Hammer.",
        file_tuples=file_tuples,
        desc_label="Bundling Crafting"
    )

def bundle_mice():
    """Bundle 6: All 1,316 Mice."""
    mice_dir = DATA_DIR / "mice"
    if not mice_dir.exists(): return None

    files = sorted(list(mice_dir.glob("*.md")), key=lambda p: p.stem.lower())
    if not files: return None

    file_tuples = [(f, "🐭 Mouse:", "Mouse") for f in files]
    return bundle_files(
        output_filename="06_mousehunt_mice.md",
        bundle_title="🐭 MouseHunt Knowledge Base: All 1,316 Mice Encyclopedia",
        bundle_desc="Ensiklopedia lengkap seluruh spesies tikus MouseHunt: Kelemahan Elemen Perangkap (Weaknesses), Umpan Keju Efektif, Lokasi Habitat, Nilai Points/Gold, dan Hadiah Drop Loot.",
        file_tuples=file_tuples,
        desc_label="Bundling Mice"
    )

def main():
    print("=" * 65)
    print("      MOUSEHUNT RAG CORPUS BUNDLER (MODULAR BUNDLES)        ")
    print("=" * 65)
    print(f"Direktori Data   : {DATA_DIR}")
    print(f"Direktori Output : {BUNDLES_DIR}\n")

    BUNDLES_DIR.mkdir(parents=True, exist_ok=True)

    results = []

    # 1. Locations
    res_loc = bundle_locations()
    if res_loc: results.append(res_loc)

    # 2. Mechanics
    res_mech = bundle_mechanics()
    if res_mech: results.append(res_mech)

    # 3. Equipment (Weapons & Bases)
    res_eq = bundle_equipment()
    if res_eq: results.append(res_eq)

    # 4. Consumables (Cheese, Charms, Potions, Special, Auras)
    res_con = bundle_consumables()
    if res_con: results.append(res_con)

    # 5. Crafting (Blueprints & Recipes)
    res_cr = bundle_crafting()
    if res_cr: results.append(res_cr)

    # 6. Mice
    res_mice = bundle_mice()
    if res_mice: results.append(res_mice)

    print("\n" + "=" * 65)
    print("                 RINGKASAN BUNDEL TERCIPTA")
    print("=" * 65)
    total_chars = 0
    for out_path, count, char_len in results:
        size_mb = out_path.stat().st_size / (1024 * 1024)
        est_tokens = char_len // 4
        total_chars += char_len
        print(f"  📄 {out_path.name}")
        print(f"     • Entitas Unik   : {count:,} entitas")
        print(f"     • Ukuran File    : {size_mb:.2f} MB")
        print(f"     • Estimasi Token : ~{est_tokens:,} tokens")
        print(f"     • Lokasi         : {out_path}")
        print("-" * 65)

    grand_mb = sum(p.stat().st_size for p, _, _ in results) / (1024 * 1024)
    grand_tokens = total_chars // 4
    print(f"  Total Ukuran Seluruh Bundel : {grand_mb:.2f} MB")
    print(f"  Total Estimasi Token        : ~{grand_tokens:,} tokens")
    print("=" * 65)
    print("\n💡 Keuntungan Bundel Terpisah Ini:")
    print("1. Equipment (Weapons & Bases) terpisah rapi untuk pertanyaan seputar setup senjata.")
    print("2. Consumables (Cheese, Charms, Potions) terpisah untuk rekomendasi umpan & charm.")
    print("3. Crafting menjadi direktori tersendiri untuk resep & blueprint.")
    print("4. Tidak ada duplikasi halaman master (ukuran file menjadi sangat ringkas & hemat token!).")
    print("5. Semua file siap Anda upload ke Google AI Studio atau NotebookLM! 🚀\n")

if __name__ == "__main__":
    main()
