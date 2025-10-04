import pandas as pd
import json

category_urls = {
    "meat": "https://handlaprivatkund.ica.se/stores/1004181/categories/k%C3%B6tt-chark-f%C3%A5gel/3ed155d4-01df-408f-bffc-f91e7404cab2?source=navigation",
    "own": "https://handlaprivatkund.ica.se/stores/1004181/categories/butikens-egna-varor/5dc3164f-038a-4202-a734-86a0bac7c427?source=navigation",
    "fish": "https://handlaprivatkund.ica.se/stores/1004181/categories/fisk-skaldjur/e32fbd57-fb20-4fdf-b1f6-f83cb990ccd8?source=navigation",
    "cheese": "https://handlaprivatkund.ica.se/stores/1004181/categories/mejeri-ost/e2ac37e6-aa68-477b-b78a-97228046b8d2?source=navigation",
    "bread": "https://handlaprivatkund.ica.se/stores/1004181/categories/br%C3%B6d-kakor/528b82cc-e3d4-43f2-9559-6e8ca9b56c2e?source=navigation",
    "vege": "https://handlaprivatkund.ica.se/stores/1004181/categories/vegetariskt/a931178f-85ab-4139-a54f-3dfe60421e36?source=navigation",
    "ready": "https://handlaprivatkund.ica.se/stores/1004181/categories/f%C3%A4rdigmat/ecfe2469-b003-4b3d-8e1d-9ef26d5c7328?source=navigation",
    "snack": "https://handlaprivatkund.ica.se/stores/1004181/categories/glass-godis-snacks/05f32791-8dc2-43cf-8230-1fcf0e05a9a9?source=navigation",
    "drink": "https://handlaprivatkund.ica.se/stores/1004181/categories/dryck/38b1e8f0-0146-4a5c-ba0c-286b8277d235?source=navigation",
    "pantry": "https://handlaprivatkund.ica.se/stores/1004181/categories/skafferi/7b81630c-9bad-4210-977d-a45aec0a5c9e?source=navigation",
    "frozen": "https://handlaprivatkund.ica.se/stores/1004181/categories/fryst/4aeec528-18cd-4b0f-9c50-21ac44e6f3e7?source=navigation",
}

# input and output file paths
for category in category_urls:
    csv_file = f"ica_category_data/ica_{category}_data.csv"
    json_file = f"ica_json_data/ica_{category}.json"

    # read CSV
    df = pd.read_csv(csv_file)

    # fixed fields
    fixed_fields = ["Name", "Price", "url"]

    # nutrition
    nutrition_fields = [col for col in df.columns if col not in fixed_fields + ["Size"]]

    products = []
    for _, row in df.iterrows():
        product = {
            "title": str(row["Name"]).strip(),
            "price": str(row["Price"]).replace(" kr", "").strip(),
            "url": str(row["url"]).strip(),
        }

        # process nutrition
        nutrition = {}
        for col in nutrition_fields:
            value = str(row[col]).strip()
            if value and value.lower() != "nan":
                nutrition[col.lower()] = value

        if nutrition:  # only add if there are nutrition facts
            product["nutrition"] = nutrition
        
        products.append(product)

    # save to JSON
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    print(f"Success! JSON file created at {json_file}")
