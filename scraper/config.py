import os
from pathlib import Path

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOCATIONS_DIR = DATA_DIR / "locations"
MICE_DIR = DATA_DIR / "mice"
ITEMS_DIR = DATA_DIR / "items"
MECHANICS_DIR = DATA_DIR / "mechanics"

# API Configuration
API_URL = "https://mhwiki.hitgrab.com/wiki/api.php"
BASE_WIKI_URL = "https://mhwiki.hitgrab.com/wiki/index.php"
USER_AGENT = "MouseHuntRAGScraper/1.0 (Educational RAG Project; https://github.com/mh-rag)"

# Polite delay between HTTP calls (seconds)
DEFAULT_DELAY = 0.15

# Categories for Items (Essential Gameplay Items only)
# Excluded: Collectibles, generic Trap Skins, Airship Cosmetics, Themes
ITEM_CATEGORIES = {
    "Weapons": "weapons",
    "Bases": "bases",
    "Cheese": "cheese",
    "Charms": "charms",
    "Crafting Items": "crafting",
    "Potions": "potions",
    "Special Items": "special",
    "Auras": "auras"
}

# Category for Mice
MICE_CATEGORY = "Mice"

# Category for Locations
LOCATIONS_CATEGORY = "Locations"

# Core Gameplay & Mechanics Pages
CORE_MECHANICS_PAGES = [
    "Location",
    "Travel",
    "Maps and Keys",
    "Shops",
    "Hunter",
    "Rank",
    "Hunter's Horn",
    "Gold",
    "Points",
    "Wisdom",
    "King",
    "Inventory",
    "Crafting",
    "Hunter's Hammer",
    "Potion",
    "Special",
    "Loot",
    "Trap Skin",
    "Aura"
]

# Functional / Stat-Altering Trap Skins (Exceptions to the cosmetic-only rule)
FUNCTIONAL_SKINS = [
    "Isle Idol Hydro Skin",
    "Isle Idol Forgotten Skin",
    "Isle Idol Tactical Skin",
    "Golem Guardian Arcane Skin",
    "Golem Guardian Forgotten Skin",
    "Golem Guardian Hydro Skin",
    "Golem Guardian Tactical Skin",
    "Golem Guardian Physical Skin",
    "Golem Guardian Shadow Skin"
]

# Pilot limits
PILOT_ITEM_LIMIT = 5
PILOT_MICE_LIMIT = 20
PILOT_LOCATION_LIMIT = 5
