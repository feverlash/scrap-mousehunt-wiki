import os
from pathlib import Path
import yaml
from typing import Dict, List, Any

from scraper.config import DATA_DIR, MICE_DIR, ITEMS_DIR

ALL_POWER_TYPES = [
    "Physical", "Tactical", "Hydro", "Arcane", "Forgotten",
    "Shadow", "Draconic", "Law", "Rift", "Parental"
]

AGGREGATES_DIR = DATA_DIR / "aggregates"

def extract_frontmatter(file_path: Path) -> Dict[str, Any]:
    """Extract YAML frontmatter from a markdown file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                return yaml.safe_load(parts[1]) or {}
    except Exception as e:
        print(f"[Warning] Failed to read frontmatter from {file_path.name}: {e}")
    return {}

def generate_aggregate_files():
    """Generate cross-entity aggregate summaries to empower complex natural queries in RAG."""
    AGGREGATES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n[AGGREGATES] Menghasilkan file ringkasan agregat di {AGGREGATES_DIR}...")

    # Collect all mice
    mice_files = list(MICE_DIR.glob("*.md")) if MICE_DIR.exists() else []
    mice_data = []
    for mf in mice_files:
        fm = extract_frontmatter(mf)
        if fm:
            mice_data.append(fm)

    # Collect all weapons
    weapons_dir = ITEMS_DIR / "weapons"
    weapon_files = list(weapons_dir.glob("*.md")) if weapons_dir.exists() else []
    weapons_data = []
    for wf in weapon_files:
        fm = extract_frontmatter(wf)
        if fm:
            weapons_data.append(fm)

    # 1. GENERATE: power_types.md
    power_type_summary = {pt: {"mice": [], "weapons": []} for pt in ALL_POWER_TYPES}
    for m in mice_data:
        for pt in m.get("effective_power_types", []):
            if pt in power_type_summary:
                power_type_summary[pt]["mice"].append(m["name"])

    for w in weapons_data:
        pt = w.get("power_type", "")
        if pt in power_type_summary:
            power_type_summary[pt]["weapons"].append(w)

    pt_md = [
        "# Panduan Komprehensif Power Types & Efektivitas Senjata",
        "\nDokumen ini menyajikan ringkasan agregat seluruh tipe kekuatan (Power Type) di MouseHunt beserta daftar tikus yang rentan terhadap masing-masing tipe dan senjata terkait. Digunakan untuk menjawab kueri lintas-entitas seperti: *'Tikus apa saja yang lemah terhadap Tactical?'* atau *'Senjata apa yang tersedia untuk tipe Hydro?'*.\n"
    ]

    for pt in ALL_POWER_TYPES:
        pt_md.append(f"## Power Type: {pt}")
        mice_list = power_type_summary[pt]["mice"]
        weap_list = power_type_summary[pt]["weapons"]

        pt_md.append(f"Senjata dengan tipe **{pt}** efektif untuk menangkap total {len(mice_list)} jenis tikus yang terdata.\n")

        pt_md.append(f"### Tikus yang Rentan terhadap {pt}")
        if mice_list:
            sorted_mice = sorted(mice_list)
            chunks = [sorted_mice[i:i+4] for i in range(0, len(sorted_mice), 4)]
            pt_md.append("| Tikus (Kolom 1) | Tikus (Kolom 2) | Tikus (Kolom 3) | Tikus (Kolom 4) |")
            pt_md.append("|---|---|---|---|")
            for c in chunks:
                while len(c) < 4:
                    c.append("-")
                pt_md.append(f"| {c[0]} | {c[1]} | {c[2]} | {c[3]} |")
        else:
            pt_md.append(f"- Belum ada data tikus yang terindeks untuk tipe {pt}.")
        pt_md.append("")

        pt_md.append(f"### Senjata Bertipe {pt}")
        if weap_list:
            pt_md.append("| Senjata | Power | Luck | Cost | Title Required |")
            pt_md.append("|---|---|---|---|---|")
            for w in weap_list:
                pt_md.append(f"| {w.get('name')} | {w.get('power', '-')} | {w.get('luck', '-')} | {w.get('cost', '-')} | {w.get('title_required', '-')} |")
        else:
            pt_md.append(f"- Belum ada senjata bertipe {pt} dalam korpus.")
        pt_md.append("\n---\n")

    with open(AGGREGATES_DIR / "power_types.md", "w", encoding="utf-8") as f:
        f.write("\n".join(pt_md))
    print(f"   [OK] Ditulis: {AGGREGATES_DIR / 'power_types.md'}")

    # 2. GENERATE: locations.md
    location_summary = {}
    for m in mice_data:
        area = m.get("primary_area", "Unknown")
        # May contain comma-separated areas
        areas = [a.strip() for a in area.split(",") if a.strip()]
        for a in areas:
            if a not in location_summary:
                location_summary[a] = []
            location_summary[a].append(m)

    loc_md = [
        "# Panduan Lokasi & Habitat Tikus MouseHunt",
        "\nDokumen ini merangkum seluruh lokasi perburuan beserta persebaran spesies tikus, hadiah poin/gold, dan keju yang efektif di tiap wilayah.\n"
    ]

    for loc, m_list in sorted(location_summary.items()):
        loc_md.append(f"## Wilayah / Lokasi: {loc}")
        loc_md.append(f"Wilayah **{loc}** dihuni oleh {len(m_list)} spesies tikus yang terdata:\n")
        loc_md.append("| Nama Tikus | Kelompok | Points | Gold | Umpan Efektif |")
        loc_md.append("|---|---|---|---|---|")
        for m in sorted(m_list, key=lambda x: x.get('points', 0), reverse=True):
            baits = ", ".join(m.get("effective_baits", ["Standard"]))
            loc_md.append(f"| {m.get('name')} | {m.get('mouse_group', '-')} | {m.get('points', 0):,} | {m.get('gold', 0):,} | {baits} |")
        loc_md.append("\n---\n")

    with open(AGGREGATES_DIR / "locations.md", "w", encoding="utf-8") as f:
        f.write("\n".join(loc_md))
    print(f"   [OK] Ditulis: {AGGREGATES_DIR / 'locations.md'}")

    # 3. GENERATE: weapons_catalog.md
    if weapons_data:
        weap_md = [
            "# Katalog Lengkap Senjata MouseHunt",
            "\nRingkasan komparasi seluruh senjata berburu berdasarkan Power Type, Power, Power Bonus, dan Luck.\n"
        ]
        weap_md.append("| Senjata | Power Type | Power | Power Bonus | Luck | Cost | Title Required |")
        weap_md.append("|---|---|---|---|---|---|---|")
        for w in sorted(weapons_data, key=lambda x: (x.get("power_type", ""), x.get("name", ""))):
            weap_md.append(f"| {w.get('name')} | {w.get('power_type', '-')} | {w.get('power', '-')} | {w.get('power_bonus', '-')} | {w.get('luck', '-')} | {w.get('cost', '-')} | {w.get('title_required', '-')} |")
        with open(AGGREGATES_DIR / "weapons_catalog.md", "w", encoding="utf-8") as f:
            f.write("\n".join(weap_md))
        print(f"   [OK] Ditulis: {AGGREGATES_DIR / 'weapons_catalog.md'}")

    print(f"[AGGREGATES SELESAI] File ringkasan agregat siap digunakan di {AGGREGATES_DIR}.\n")

if __name__ == "__main__":
    generate_aggregate_files()
