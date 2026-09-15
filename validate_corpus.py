import json
import re
from pathlib import Path
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
TAXONOMY_FILE = PROJECT_ROOT / "taxonomy.json"

MICE_MANDATORY_HEADINGS = [
    "## Overview",
    "## Attributes",
    "## Weakness",
    "## Effective Baits",
    "## Notes"
]

ITEMS_MANDATORY_HEADINGS = [
    "## Overview",
    "## Attributes",
    "## Acquisition & Crafting",
    "## Usage & Strategy",
    "## Notes"
]

def load_taxonomy():
    if TAXONOMY_FILE.exists():
        with open(TAXONOMY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def validate_file(file_path: Path, expected_headings: list, taxonomy: dict):
    issues = []
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Check YAML Frontmatter
    if not content.startswith("---"):
        issues.append("Frontmatter YAML tidak ditemukan di awal dokumen.")
        return issues

    parts = content.split("---", 2)
    if len(parts) < 3:
        issues.append("Format penutup Frontmatter (---) tidak lengkap.")
        return issues

    try:
        fm = yaml.safe_load(parts[1])
        if not isinstance(fm, dict):
            issues.append("Frontmatter bukan dictionary valid.")
    except Exception as e:
        issues.append(f"Gagal mem-parse YAML frontmatter: {e}")
        return issues

    body = parts[2]

    # 2. Check Title (# Title)
    if not re.search(r'^#\s+.+', body, re.MULTILINE):
        issues.append("Heading tingkat 1 (# Judul) tidak ditemukan.")

    # 3. Check Mandatory Headings
    for h in expected_headings:
        if h not in body:
            issues.append(f"Heading wajib '{h}' tidak ditemukan.")

    # 4. Context Check: Entity name should be mentioned in Overview
    name = fm.get("name", file_path.stem)
    overview_match = re.search(r'## Overview\s*\n(.*?)(?=\n##|\Z)', body, re.DOTALL)
    if overview_match:
        overview_text = overview_match.group(1).strip()
        if name.lower() not in overview_text.lower():
            issues.append(f"Nama entitas '{name}' tidak disebut secara eksplisit pada bagian Overview.")

    # 5. Taxonomy Validation
    valid_power_types = taxonomy.get("power_types", {})
    if "effective_power_types" in fm:
        for pt in fm["effective_power_types"]:
            if pt not in valid_power_types:
                issues.append(f"Power type '{pt}' tidak terdaftar dalam taxonomy.json.")

    return issues

def main():
    print("=" * 65)
    print("      LINTER & VALIDATOR KONSISTENSI KORPUS RAG MOUSEHUNT")
    print("=" * 65)

    taxonomy = load_taxonomy()
    if not taxonomy:
        print("[Warning] taxonomy.json tidak ditemukan atau kosong.")

    mice_files = list((DATA_DIR / "mice").glob("*.md")) if (DATA_DIR / "mice").exists() else []
    item_files = list((DATA_DIR / "items").rglob("*.md")) if (DATA_DIR / "items").exists() else []

    total_files = len(mice_files) + len(item_files)
    if total_files == 0:
        print(f"[Info] Tidak ada file Markdown di {DATA_DIR}. Silakan jalankan scraper terlebih dahulu.")
        return

    print(f"[*] Memeriksa {len(mice_files)} file tikus dan {len(item_files)} file item...")

    passed = 0
    failed = 0
    error_log = {}

    # Validate Mice
    for mf in mice_files:
        issues = validate_file(mf, MICE_MANDATORY_HEADINGS, taxonomy)
        if not issues:
            passed += 1
        else:
            failed += 1
            error_log[mf.name] = issues

    # Validate Items
    for item_f in item_files:
        issues = validate_file(item_f, ITEMS_MANDATORY_HEADINGS, taxonomy)
        if not issues:
            passed += 1
        else:
            failed += 1
            error_log[item_f.name] = issues

    compliance_rate = (passed / total_files) * 100 if total_files > 0 else 0

    print("\n" + "-" * 65)
    print(f"  • Total File Diperiksa : {total_files}")
    print(f"  • Lolos Validasi       : {passed} file")
    print(f"  • Tidak Sesuai Template: {failed} file")
    print(f"  • Tingkat Kepatuhan    : {compliance_rate:.1f}%")
    print("-" * 65)

    if error_log:
        print("\n[DAFTAR KETIDAKSESUAIAN]:")
        for fname, issues in list(error_log.items())[:10]:
            print(f"\n📄 {fname}:")
            for iss in issues:
                print(f"   - {iss}")
        if len(error_log) > 10:
            print(f"\n... dan {len(error_log) - 10} file lainnya.")
        print("\nTip: Jalankan `python run_scraper.py --mode pilot --force` setelah pembaruan parser.")
    else:
        print("\n[SUKSES] Semua file 100% mematuhi template wajib, taxonomy, dan standar RAG! ✨\n")

if __name__ == "__main__":
    main()
