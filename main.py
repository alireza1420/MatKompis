from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from pathlib import Path
import json
import csv
import os

from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Create FastAPI app
app = FastAPI(title="SmartRecipe MVP")

# Allow frontend (Gradio) to call FastAPI locally
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# LOAD PRODUCTS

def load_hemkop_jsons(folder: Path):
    products = []
    for file in folder.glob("hemkop_*.json"):
        try:
            with open(file, encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    name = item.get("title")
                    nutrition = item.get("nutrition", {})
                    products.append({
                        "name": name,
                        "store": "Hemköp",
                        "price": item.get("price"),
                        "nutrition": nutrition
                    })
        except Exception as e:
            print(f"Error reading {file}: {e}")
    return products

def load_ica_csvs(folder: Path):
    products = []
    for file in folder.glob("ica_*.csv"):
        try:
            with open(file, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row.get("Name")
                    nutrition = {
                        k: v for k, v in row.items()
                        if k and any(word in k.lower() for word in ["energi", "fett", "protein", "salt", "kolhydrat", "fiber"])
                    }
                    products.append({
                        "name": name,
                        "store": "ICA",
                        "price": row.get("Price"),
                        "nutrition": nutrition
                    })
        except Exception as e:
            print(f"Error reading {file}: {e}")
    return products

def find_price(product_name):
    term = translate_term(product_name)
    matches = [p for p in PRODUCTS if term in p["name"].lower()]
    if matches:
        p = matches[0]
        return f"{p['name']} costs {p['price']} ({p['store']})"
    return f"Sorry, I couldn't find price for {product_name}."



TRANSLATION_MAP = {
    "salmon": "lax",
    "chicken": "kyckling",
    "pork": "fläsk",
    "beef": "nöt",
    "rice": "ris",
    "bread": "bröd",
    "apple": "äpple",
    "tofu": "tofu",  # same in both
}

def translate_term(term):
    return TRANSLATION_MAP.get(term.lower(), term.lower())


def load_all_products():
    base = Path(__file__).parent / "data"
    hemkop_data = load_hemkop_jsons(base)
    ica_data = load_ica_csvs(base)
    products = hemkop_data + ica_data
    print(f"Loaded {len(products)} products ({len(hemkop_data)} Hemköp, {len(ica_data)} ICA)")
    return products

PRODUCTS = load_all_products()

# GEMINI INTENT CLASSIFIER

import re, json

import json, re
import google.generativeai as genai

import json, re
import google.generativeai as genai

def classify(query: str):
    # Use a supported model from your list
    model = genai.GenerativeModel("models/gemini-2.5-flash")

    prompt = f"""
You are a strict JSON generator.

Your job is to classify food-related questions into one of these intents:

1. "product_nutrient" – ask about nutrient values (protein, calories, etc.)
2. "price_query" – ask about cost or price
3. "recipe_query" – ask for a list of recipes using an ingredient
4. "recipe_detail" – ask for full details of a specific recipe
5. "meal_recommendation" – ask for meals or recipes with dietary preferences (e.g. vegan, vegetarian, pescatarian, meat-based, high protein, low carb)
6. "unknown" – everything else

Extract slots:
- meal_recommendation: diet, nutrient, level (e.g. high, low), meal_type (optional: breakfast, lunch, dinner)
- recipe_query: ingredient
- recipe_detail: recipe_title
- product_nutrient: product, nutrient
- price_query: product

Return only JSON, no text.

Examples:
{{"intent": "meal_recommendation", "slots": {{"diet": "vegan", "nutrient": "protein", "level": "high"}}}}
{{"intent": "meal_recommendation", "slots": {{"diet": "pescatarian", "ingredient": "salmon"}}}}

Query: "{query}"
"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        print("Raw Gemini output:", text)

        import re, json
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group(0)
        data = json.loads(text)

        q_lower = query.lower().strip()

        # Rule-based fallback: "show", "details", "more info", "how to make"
        if any(kw in q_lower for kw in ["show", "details", "more info", "how to make", "recipe for", "get info"]):
            # Try extract a title (everything after keyword)
            title_part = q_lower
            for kw in ["show", "details", "more info about", "get info about", "how to make", "recipe for"]:
                if kw in q_lower:
                    title_part = q_lower.split(kw, 1)[-1].strip()
                    break
            data = {"intent": "recipe_detail", "slots": {"recipe_title": title_part}}


        q_lower = query.lower().strip()
        if q_lower.startswith(("show ", "open ", "details ", "view ")):
            tail = q_lower.split(" ", 1)[1].strip('" ')
            data = {"intent": "recipe_detail", "slots": {"recipe_title": tail}}

        # Tiny validation step: ensure ingredient matches query
        if data.get("intent") == "recipe_query":
            slots = data.setdefault("slots", {})
            ingr = slots.get("ingredient")
            q_lower = query.lower()
            if not ingr or ingr.lower() not in q_lower:
                # fallback: find a food-like word from the query
                words = [w for w in q_lower.split() if w.isalpha()]
                slots["ingredient"] = words[-1] if words else "ingredient"

        return data
    except Exception as e:
        print("Classification error:", e)
        return {"intent": "unknown", "slots": {}}


# ANSWER BUILDER 

def find_product(name: str):
    for p in PRODUCTS:
        if name.lower() in p["name"].lower():
            return p
    return None

def answer_query(intent: str, slots: Dict[str, Any]) -> str:
    if intent == "product_nutrient":
        product_name = slots.get("product")
        nutrient = slots.get("nutrient")
        if not product_name or not nutrient:
            return "Please specify a product and nutrient."
        product = find_product(product_name)
        if not product:
            return f"Sorry, I couldn’t find {product_name}."
        value = None
        for k, v in product["nutrition"].items():
            if nutrient.lower() in k.lower():
                value = v
                break
        if value:
            return f"{nutrient.capitalize()} in {product['name']}: {value} per 100 g."
        return f"Sorry, I couldn't find {nutrient} info for {product['name']}."
    
    elif intent == "price_query":
        product_name = slots.get("product")
        if not product_name:
            return "Please specify a product name."
        return find_price(product_name)

    
    elif intent == "recipe_query":
        ingredient = slots.get("ingredient")
        if not ingredient:
            return "Please specify an ingredient or type of meal (e.g., 'recipes with chicken')."
        hits = list_recipes_by_ingredient(ingredient, limit=5)
        if not hits:
            return f"Sorry, I couldn’t find recipes with {ingredient}."
        # Titles only
        lines = [f"{i+1}. {h['title']} — id: {h['id']}" for i, h in enumerate(hits)]
        return (
            f"Here are some recipes with {ingredient}:\n"
            + "\n".join(lines)
            + "\n\nAsk: 'show <title>' or 'show <id>' to see full details.")
    
    elif intent == "meal_recommendation":
        diet = slots.get("diet")
        nutrient = slots.get("nutrient")
        level = slots.get("level")
        meal_type = slots.get("meal_type")

        if not diet:
            return "Please specify a dietary preference (e.g., vegan, vegetarian, pescatarian)."

        # Find recipes matching diet
        recipes = filter_recipes_by_diet(diet)

        if nutrient and level == "high":
            # Filter further using product nutrients (optional)
            recipes = filter_high_nutrient_recipes(recipes, nutrient)

        if meal_type:
            recipes = [r for r in recipes if meal_type.lower() in str(r.get("title", "")).lower()]

        if not recipes:
            return f"Sorry, I couldn’t find any {diet} recipes."

        lines = [f"{i+1}. 🍽️ {r['title']}" for i, r in enumerate(recipes[:5])]
        return f"🌱 Here are some {diet} recipes" + (f" rich in {nutrient}" if nutrient else "") + ":\n" + "\n".join(lines)

    elif intent == "recipe_query":
        ingredient = slots.get("ingredient")
        if not ingredient:
            return "Please specify an ingredient or type of meal (e.g., 'recipes with chicken')."

        hits = list_recipes_by_ingredient(ingredient, limit=5)
        if not hits:
            return f"Sorry, I couldn’t find recipes with {ingredient}."

        # Titles only (no ids, no instructions)
        lines = [f"{i+1}. 🍽️ {h['title']}" for i, h in enumerate(hits)]

        # Friendly follow-up hint
        follow_ups = (
            "\n\n💡 Tip: You can ask things like:\n"
            "• *Show Lentil Burgers*\n"
            "• *Show Miso-Butter Roast Chicken With Acorn Squash Panzanella*")

        return f"👨‍🍳 Recipe ideas:\nHere are some recipes with **{ingredient}**:\n" + "\n".join(lines) + follow_ups


    elif intent == "recipe_detail":
        rid_or_title = slots.get("recipe_title") or slots.get("recipe_id") or ""
        if not rid_or_title:
            return "Tell me which recipe: 'show <title>' or 'show <id>'."
        # accept id or partial title
        r = next((x for x in RECIPES if x["id"] == rid_or_title), None)
        if not r:
            r = find_recipe_by_id_or_title(rid_or_title)
        if not r:
            return f"Couldn’t find a recipe matching '{rid_or_title}'."
        payload = recipe_detail_payload(r)
        # format a friendly text answer
        out = [f"🍽️ {payload['title']}\n",
            "Ingredients:"]
        out += [f"• {ing}" for ing in payload["ingredients"]]
        out += ["\nSteps:"]
        out += [f"{i+1}) {s}" for i, s in enumerate(payload["steps"])]
        out += ["\nWhere to buy (best match):"]
        for link in payload["where_to_buy"]:
            if link["product_name"]:
                out.append(f"• {link['ingredient']} → {link['product_name']} ({link['store']}) {link['price']} | {link['url']}")
            else:
                out.append(f"• {link['ingredient']} → (no match)")
        return "\n".join(out)
    
    return "I’m not sure how to help with that yet."

# API ENDPOINT

class AskResponse(BaseModel):
    intent: str
    answer: str
    slots: Optional[Dict[str, Any]] = None

@app.get("/ask", response_model=AskResponse)
def ask(q: str = Query(..., description="User query")):
    route = classify(q)
    print("🔍 Route:", route)
    intent = route.get("intent", "unknown")
    slots = route.get("slots", {})
    answer = answer_query(intent, slots)
    return {"intent": intent, "answer": answer, "slots": slots}

# Root 

@app.get("/")
def root():
    return {"message": "SmartRecipe API is running 🚀"}

import pandas as pd

# LOAD RECIPES
def load_recipes():
    base = Path.cwd() / "recipes.csv"
    recipes = []
    try:
        df = pd.read_csv(base)
        for _, row in df.iterrows():
            recipes.append({
                "title": row["Title"],
                "ingredients": row["Ingredients"],
                "instructions": row["Instructions"],
                "image": row.get("Image_Name", ""),
                "cleaned_ingredients": row.get("Cleaned_Ingredients", "")
            })
        print(f"Loaded {len(recipes)} recipes")
    except Exception as e:
        print("Error loading recipes:", e)
    return recipes

RECIPES = load_recipes()

import re, ast

def slugify(title: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", title.lower()).strip("-")
    return s[:80]

def parse_ingredients_field(val):
    """Recipes CSV stores ingredients as a python-ish list string."""
    if isinstance(val, list):
        return val
    s = str(val)
    try:
        out = ast.literal_eval(s)
        if isinstance(out, list):
            return [str(x) for x in out]
    except Exception:
        pass
    # fallback: split by commas
    return [x.strip() for x in s.split(",") if x.strip()]

def split_instructions(s: str):
    raw = str(s).replace("\r\n", "\n").replace("\r", "\n")
    parts = [p.strip(" \t") for p in raw.split("\n") if p.strip()]
    if len(parts) <= 1:
        # fallback to sentence-ish split
        parts = [p.strip() for p in re.split(r"\.\s+", raw) if p.strip()]
    return parts

# Precompute IDs for recipes
for r in RECIPES:
    r["id"] = slugify(str(r["title"] if "title" in r else r.get("Title", "")) or str(r.get("title","")))
    if not r["id"]:
        r["id"] = slugify(r.get("Title","untitled"))

def _rec_title(r):
    return r.get("title") or r.get("Title") or "Untitled"

def list_recipes_by_ingredient(ingredient: str, limit: int = 5):
    key = ingredient.lower()
    results = []
    for r in RECIPES:
        # Only search ingredients & cleaned_ingredients
        ing_field = str(r.get("ingredients") or r.get("Ingredients") or "")
        clean_field = str(r.get("cleaned_ingredients") or r.get("Cleaned_Ingredients") or "")
        title_field = str(_rec_title(r)).lower()

        if key in ing_field.lower() or key in clean_field.lower() or key in title_field:
            results.append({"id": r["id"], "title": _rec_title(r)})

    # De-duplicate and limit
    seen = set()
    deduped = []
    for x in results:
        if x["id"] not in seen:
            deduped.append(x)
            seen.add(x["id"])
    return deduped[:limit]


def find_recipe_by_id_or_title(q: str):
    ql = str(q).lower().strip()
    best = None
    best_score = 0
    for r in RECIPES:
        title = _rec_title(r)
        # 🔹 Ensure it's always a string
        title_str = str(title) if not isinstance(title, float) else ""
        tl = title_str.lower()
        # 🔹 Simple overlap score
        score = 0
        if ql in tl:
            score += 3
        # 🔹 Token overlap
        tokens = set(re.findall(r"[a-z0-9]+", ql))
        score += len(tokens & set(re.findall(r"[a-z0-9]+", tl)))
        if score > best_score:
            best_score = score
            best = r
    return best
def filter_recipes_by_diet(diet: str):
    diet = diet.lower()
    results = []

    # Define diet keywords
    vegan_kw = ["vegan", "plant-based"]
    vegetarian_kw = ["vegetarian", "ovo-lacto", "meat-free"]
    pesc_kw = ["fish", "pescatarian", "salmon", "cod", "shrimp"]
    meat_kw = ["chicken", "beef", "pork", "meat"]

    for r in RECIPES:
        title = str(r.get("Title") or r.get("title") or "").lower()
        ingredients = str(r.get("Ingredients") or r.get("ingredients") or "").lower()

        if diet == "vegan":
            if any(kw in title or kw in ingredients for kw in vegan_kw):
                results.append(r)
        elif diet == "vegetarian":
            if any(kw in title or kw in ingredients for kw in vegetarian_kw):
                results.append(r)
        elif diet == "pescatarian":
            if any(kw in title or kw in ingredients for kw in pesc_kw):
                results.append(r)
        elif diet == "meat":
            if any(kw in title or kw in ingredients for kw in meat_kw):
                results.append(r)
    return results

def filter_high_nutrient_recipes(recipes, nutrient="protein", threshold=10):
    results = []
    for r in recipes:
        ingredients = r.get("Cleaned_Ingredients") or r.get("Ingredients") or ""
        # crude check — match nutrient-rich ingredients
        for prod in PRODUCTS:
            if any(name.lower() in ingredients.lower() for name in [prod.get("title","")]):
                nutri = prod.get("nutrition", {}).get(nutrient)
                if nutri:
                    val = float(re.findall(r"\d+", str(nutri))[0])
                    if val >= threshold:
                        results.append(r)
                        break
    return results

# --- map ingredients to store products ---

def normalize_token(s: str):
    s = s.lower()
    s = re.sub(r"\d+([.,]\d+)?\s*(kg|g|ml|l|tbsp|tsp|dl|pack|pkt|st|x)", " ", s)
    s = re.sub(r"[^\wÅÄÖåäö]+", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def key_from_ingredient(ing: str):
    s = normalize_token(ing)
    # heuristics: take first 1–2 words that look food-like
    words = [w for w in s.split() if len(w) > 2][:2]
    return " ".join(words) if words else s

def find_best_product(query_key: str):
    q = query_key.lower()
    best = None
    best_score = 0
    for p in PRODUCTS:
        name = p["name"].lower()
        score = 0
        if q and q in name: score += 3
        # token overlap
        tq = set(q.split())
        score += len(tq & set(name.split()))
        if score > best_score:
            best_score = score; best = p
    return best

def map_ingredients_to_products(ingredients: list):
    mapped = []
    for ing in ingredients:
        k = key_from_ingredient(ing)
        prod = find_best_product(k)
        if prod:
            mapped.append({
                "ingredient": ing,
                "product_name": prod["name"],
                "store": prod["store"],
                "price": prod.get("price"),
                "url": prod.get("url", "")
            })
        else:
            mapped.append({"ingredient": ing, "product_name": None, "store": None, "price": None, "url": None})
    return mapped

def recipe_detail_payload(r):
    title = _rec_title(r)
    ingredients = parse_ingredients_field(r.get("ingredients") or r.get("Ingredients",""))
    steps = split_instructions(r.get("instructions") or r.get("Instructions",""))
    links = map_ingredients_to_products(ingredients)
    return {
        "id": r["id"],
        "title": title,
        "ingredients": ingredients,
        "steps": steps,
        "where_to_buy": links
    }


def find_recipes_by_ingredient(keyword: str):
    results = []
    for r in RECIPES:
        if keyword.lower() in str(r["ingredients"]).lower():
            results.append(r)
    return results[:5]  # return top 5 matches

