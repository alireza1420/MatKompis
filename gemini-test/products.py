

from pathlib import Path
import json

# points to "data/hemkop_bird.json" 
DATA_PATH = Path.cwd() / "data" / "hemkop_bird.json"

with open(DATA_PATH, encoding="utf-8") as f:
    PRODUCTS = json.load(f)

print(f"Loaded {len(PRODUCTS)} products.")

def find_product(name: str):
    name_lower = name.lower()
    for prod in PRODUCTS:
        if name_lower in prod["name"].lower():
            return prod
    return None

def get_nutrient(name: str, nutrient: str):
    prod = find_product(name)
    if not prod:
        return None, f"Product '{name}' not found."
    per100 = prod["per_100g"]
    key = nutrient.lower().replace(" ", "_")
    # crude mapping
    aliases = {
        "protein": "protein_g",
        "fat": "fat_g",
        "carbs": "carbs_g",
        "sugar": "sugars_g",
        "energy": "energy_kcal",
        "calories": "energy_kcal"
    }
    key = aliases.get(key, key)
    if key not in per100:
        return None, f"Nutrient '{nutrient}' not found."
    return per100[key], f"{nutrient.title()} in {prod['name']}: {per100[key]} per 100 g."
