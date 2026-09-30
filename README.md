# MouseHunt Wiki Scraper & Corpus Suite (RAG AI & Lore Bible)

Repositori ini menyediakan dua pipeline scraping dan bundling terpisah untuk mengonversi data dari **MouseHunt Wiki** menjadi basis data Markdown terstruktur. Setiap pipeline dioptimalkan untuk use case kecerdasan buatan (AI) yang berbeda:

1. **Scraper Gameplay & Taktik (`run_scraper.py` + `bundle_corpus.py`)**: Dioptimalkan untuk **RAG AI Gameplay**, asisten kalkulator perburuan, panduan progresi pangkat, efektivitas keju, dan kelemahan elemen perangkap (dibersihkan dari trivia dan kosmetik).
2. **Scraper Lore & Worldbuilding (`run_scraper_lore.py` + `bundle.py`)**: Dioptimalkan untuk **AI Naratif & Fanfiksi**, agen roleplay karakter, ensiklopedia cerita (bestiary lore, jurnal Sir Plankrun, sejarah persenjataan, travelogue wilayah, profil tokoh, dan kosmologi semesta Gnawnia).

---

## ⚖️ Perbandingan Kedua Pipeline

| Aspek | Scraper 1: Gameplay & Taktik | Scraper 2: Lore & Worldbuilding |
| :--- | :--- | :--- |
| **Script Scraper** | `run_scraper.py` | `run_scraper_lore.py` |
| **Script Bundler** | `bundle_corpus.py` | `bundle.py` |
| **Folder Mentah** | `data/` (`locations/`, `mechanics/`, `items/`, `mice/`) | `lore/` (`A_plankrun_journal/` s.d. `F_world_mechanics/`) |
| **Folder Bundel** | `bundles/` (6 file master) | `bundles_lore/` (Partisi bestiary, 6 komponen, atau master bible) |
| **Fokus Konten** | Tabel stat, kelemahan, umpan, lokasi drop, syarat rank, HUD area | Cerita latar, deskripsi ekologi, kepribadian, jurnal fiksi, dialog |
| **Filter Data** | Menghapus trivia, kosmetik murni, dan potongan jurnal fiksi | Menghapus log versi/patch, navigasi wiki, dan UI teknis |
| **Target AI** | RAG Gameplay Assistant, Decision Support, Hunting Advisor | AI Penulis Narasi, Agen Fanfiksi, Worldbuilding Assistant |

---

## 🎮 Scraper 1: Taktik & Mekanik Gameplay

Scraper ini menghasilkan dataset Markdown murni berbasis taktik permainan yang siap di-ingest ke sistem RAG AI.

### 1. Cakupan Data:
- **Locations (`data/locations/`)**: Seluruh wilayah berburu (syarat rank, peta travel/kunci Cartographer, daftar tikus per area, toko, dan mekanik HUD area) - **tanpa History and Trivia**.
- **Mice (`data/mice/`)**: Seluruh 1.316 spesies tikus (kelemahan elemen perangkap, preferensi keju, lokasi bertengger, dan drop loot) - **tanpa History and Trivia**.
- **Core Mechanics & Progression (`data/mechanics/`)**:
  - `Travel`, `Maps and Keys`, `Shops`
  - `Rank` (progresi pangkat Novice hingga Elder)
  - `Hunter`, `Hunter's Horn`, `Hunter's Hammer`, `Crafting`
  - `Gold`, `Points`, `Wisdom`, `King`, `Inventory`, `Loot`
  - `Aura` (Spooky, Slayer, Chrome, Lightning, Festive Aura)
  - `Trap Skin` umum + **Skin Fungsional yang Mengubah Stats/Power Type**:
    * *Isle Idol Trap Skins* (Hydro, Forgotten, Tactical)
    * *Golem Guardian Trap Modules* (Arcane, Forgotten, Hydro, Tactical, Physical, Shadow)
- **Items (`data/items/`)**:
  - `Weapons` (Perangkap berburu)
  - `Bases` (Base perangkap)
  - `Cheese` (Semua umpan keju & attraction rate)
  - `Charms` (Stats tambahan & konsumsi per hunt)
  - `Potions` (Resep ramuan konversi)
  - `Crafting Items` (Bahan baku & blueprint)
  - `Special Items` (Convertibles, chests, map pieces)
  - `Auras`

### 2. Dieliminasi (Noise & Kosmetik Murni):
- ❌ **History and Trivia** (dihapus dari semua halaman: tanggal rilis event lama dan trivia visual).
- ❌ **Trap Skins Biasa** (378 skin visual biasa yang tidak mengubah stats).
- ❌ **Airship Cosmetics** (dekorasi gambar pesawat profil).
- ❌ **Collectibles** (pajangan inventaris tanpa fungsi berburu).
- ❌ **Torn Pages of Plankrun's Journal** (teks cerita novel fiksi).
- ❌ **Jargon & Journal Themes / Theme Scraps**.

### 3. Cara Menjalankan Scraper 1:
```powershell
# Uji coba pilot (sampel lokasi, mekanik, items, & tikus)
python run_scraper.py --mode pilot --force

# Eksekusi penuh seluruh katalog wiki
python run_scraper.py --mode full --force

# Mode spesifik per kategori
python run_scraper.py --mode locations
python run_scraper.py --mode mechanics
python run_scraper.py --mode items
python run_scraper.py --mode mice
```

### 4. Bundler Korpus Gameplay (`bundle_corpus.py`):
Menggabungkan ribuan file di `data/` menjadi 6 bundel tematik siap pakai di direktori `bundles/`:
```powershell
python bundle_corpus.py
```
Daftar file output:
1. `01_mousehunt_locations.md` (Wilayah berburu, syarat rank, HUD, dan toko)
2. `02_mousehunt_mechanics.md` (Aturan mekanik, progresi rank, travel, auras, & skin fungsional)
3. `03_mousehunt_equipment.md` (Katalog perlengkapan: Weapons & Bases)
4. `04_mousehunt_consumables.md` (Katalog bahan habis pakai: Cheese, Charms, Potions, Special Items, Auras)
5. `05_mousehunt_crafting.md` (Katalog perakitan: Blueprints, suku cadang, dan bahan crafting)
6. `06_mousehunt_mice.md` (Ensiklopedia seluruh 1.316 jenis tikus)

---

## 📜 Scraper 2: Lore, Narasi & Worldbuilding

Scraper ini didesain khusus untuk mengekstraksi esensi naratif, cerita sejarah, kepribadian karakter, ekologi makhluk, dan kosmologi semesta MouseHunt.

### 1. Cakupan 6 Komponen Lore:
- **Komponen A (`lore/A_plankrun_journal/`)**: Kronik Sir Plankrun (pemburu pertama di Gnawnia), berisi pecahan jurnal ekspedisi (*Torn Pages*) dan catatan lapangan perburuan.
- **Komponen B (`lore/B_mice_lore/`)**: Bestiari seluruh spesies tikus, memuat deskripsi kepribadian, latar belakang cerita, ekologi habitat, dan dinamika faksi.
- **Komponen C (`lore/C_equipment_lore/`)**: Gudang persenjataan & rekayasa perangkap (teknologi uap Digby, kristal magis Arcane, modifikasi Hydro, dan arsitektur base pertahanan).
- **Komponen D (`lore/D_world_regions/`)**: Travelogue geografi dan atmosfer naratif (suasana pedesaan Gnawnia, reruntuhan kuno Furoma, benteng Fort Rox, hingga keganjilan dimensi Rift).
- **Komponen E (`lore/E_key_characters/`)**: Dramatis Personae (profil The King, Larry the Friendly Knight, pedagang Ronza si penjelajah udara, penyihir catur Zugzwang, bos legendaris seperti Warmonger dan Ful'Mina, serta faksi-faksi perang).
- **Komponen F (`lore/F_world_mechanics/`)**: Hukum alam dan filosofi semesta (sakralitas tiupan Hunter's Horn, kode kehormatan pangkat Novice-Elder, tradisi resep keju mistis, dan 10 elemen daya perangkap).

### 2. Fitur Unggulan Scraper 2:
- **Mode Sumber Hybrid (`--source hybrid`)**: Memeriksa file lokal di `data/` terlebih dahulu untuk mengekstraksi teks cerita. Jika file belum ada atau belum lengkap, scraper akan mengunduh langsung dari MediaWiki API secara otomatis.
- **Pembersihan Cerdas**: Menyingkirkan tabel revisi/patch teknis dan elemen UI navigasi, tetapi mempertahankan kutipan catatan sejarah, dialog cerita, dan lore infobox.
- **Standarisasi Tanda Baca**: Menormalisasi semua tanda pisah menjadi tanda hubung standar `-` untuk kompatibilitas tokenizer model bahasa dan kemudahan pembacaan.

### 3. Cara Menjalankan Scraper 2:
```powershell
# Eksekusi seluruh komponen A s.d. F (sumber hybrid, menimpa file lama jika diinginkan)
python run_scraper_lore.py --mode all --source hybrid --force

# Eksekusi komponen tertentu
python run_scraper_lore.py --mode A          # atau --mode plankrun
python run_scraper_lore.py --mode B          # atau --mode mice
python run_scraper_lore.py --mode C          # atau --mode equipment
python run_scraper_lore.py --mode D          # atau --mode regions
python run_scraper_lore.py --mode E          # atau --mode characters
python run_scraper_lore.py --mode F          # atau --mode mechanics

# Eksekusi dengan batas sampel (misal 10 file per kategori untuk pengujian)
python run_scraper_lore.py --mode all --limit 10

# Memaksa unduh ulang dari wiki daring tanpa menggunakan cache lokal
python run_scraper_lore.py --mode all --source online --force
```

### 4. Bundler Korpus Lore (`bundle.py`):
Mengompilasi file-file di folder `lore/` ke dalam direktori `bundles_lore/`:
```powershell
# Bundel seluruh komponen (bestiary tikus otomatis dibagi rapi berdasarkan abjad)
python bundle.py

# Bundel semua komponen sekaligus menghasilkan satu file utuh Master Lore Bible
python bundle.py --all-in-one

# Opsi kustomisasi partisi bestiary tikus (misal per 200 entitas)
python bundle.py --component B --mice-chunk-size 200

# Menyatukan seluruh tikus menjadi satu file monolithic besar
python bundle.py --component B --mice-monolithic
```

Struktur hasil di `bundles_lore/`:
1. `01_plankrun_chronicles.md` (Catatan harian & jurnal ekspedisi Plankrun)
2. `02_mice_bestiary_part1_A-C.md` s.d. `part6_T-Z.md` (Bestiari naratif tikus terpartisi menurut abjad)
3. `03_equipment_armory_lore.md` (Latar belakang teknologi senjata & base)
4. `04_world_regions_travelogue.md` (Catatan perjalanan & geografi wilayah)
5. `05_dramatis_personae_factions.md` (Profil tokoh kunci, entitas legendaris, & faksi)
6. `06_world_laws_and_mechanics.md` (Hukum dunia, horn, pangkat, & kosmologi perburuan)
7. *(Opsional)* `00_mousehunt_lore_bible.md` (Kompilasi master seluruh cerita dalam satu berkas)

---

## 📁 Struktur Direktori Proyek

```text
d:\Data Analyst\Latihan Scraping\Mousehunt wiki\
├── data/                       # [Scraper 1] Data gameplay & taktik per entitas
│   ├── locations/              # Data lokasi & HUD perburuan
│   ├── mechanics/              # Mekanik inti, progresi rank, & skin fungsional
│   ├── items/                  # Senjata, base, keju, charm, potion, & crafting
│   └── mice/                   # 1.316 file tikus (kelemahan, umpan, loot)
│
├── lore/                       # [Scraper 2] Data naratif & cerita per entitas
│   ├── A_plankrun_journal/     # Rekaman jurnal & catatan Sir Plankrun
│   ├── B_mice_lore/            # Deskripsi ekologi & cerita spesies tikus
│   ├── C_equipment_lore/       # Lore teknologi senjata & base pertahanan
│   ├── D_world_regions/        # Narasi atmosfer & geografi wilayah
│   ├── E_key_characters/      # Profil tokoh, raja, Ronza, faksi & bos mitos
│   └── F_world_mechanics/      # Aturan semesta, tradisi horn, elemen & keju
│
├── bundles/                    # Hasil kompilasi bundel gameplay (bundle_corpus.py)
│   ├── 01_mousehunt_locations.md
│   ├── 02_mousehunt_mechanics.md
│   ├── 03_mousehunt_equipment.md
│   ├── 04_mousehunt_consumables.md
│   ├── 05_mousehunt_crafting.md
│   └── 06_mousehunt_mice.md
│
├── bundles_lore/               # Hasil kompilasi bundel naratif (bundle.py)
│   ├── 00_mousehunt_lore_bible.md          # (Opsional via --all-in-one)
│   ├── 01_plankrun_chronicles.md
│   ├── 02_mice_bestiary_part1_A-C.md
│   ├── 02_mice_bestiary_part2_D-H.md
│   ├── 02_mice_bestiary_part3_I-M.md
│   ├── 02_mice_bestiary_part4_N-R.md
│   ├── 02_mice_bestiary_part5_S.md
│   ├── 02_mice_bestiary_part6_T-Z.md
│   ├── 03_equipment_armory_lore.md
│   ├── 04_world_regions_travelogue.md
│   ├── 05_dramatis_personae_factions.md
│   └── 06_world_laws_and_mechanics.md
│
├── scraper/                    # Modul inti pemrosesan data & API
│   ├── api_client.py           # Klien MediaWiki API dengan rate limit terkontrol
│   ├── config.py               # Konfigurasi kategori item, URL, & folder
│   ├── parser.py               # Parser HTML wiki ke Markdown taktis gameplay
│   ├── lore_extractor.py       # Ekstraktor teks narasi, infobox, & normalisasi tanda baca
│   ├── aggregates.py           # Agregator tabel master
│   ├── scrape_locations.py     # Parser lokasi gameplay
│   ├── scrape_mechanics.py     # Parser mekanik gameplay
│   ├── scrape_items.py         # Parser items gameplay
│   └── scrape_mice.py          # Parser tikus gameplay
│
├── run_scraper.py              # CLI Runner: Scraper 1 (Gameplay & Taktik)
├── run_scraper_lore.py         # CLI Runner: Scraper 2 (Lore & Fanfiksi)
├── bundle_corpus.py            # Bundler: Kompilasi data/ ke bundles/
├── bundle.py                   # Bundler: Kompilasi lore/ ke bundles_lore/
├── validate_corpus.py          # Script validasi heading & struktur korpus
├── taxonomy.json               # Skema taksonomi kategori
└── requirements.txt            # Dependensi Python
```

---

## 🛠️ Instalasi & Prasyarat

Pastikan Python 3.9+ telah terpasang di sistem Anda.

1. Pasang paket dependensi:
```powershell
pip install -r requirements.txt
```

2. Validasi integritas berkas hasil scraping (opsional):
```powershell
python validate_corpus.py
```