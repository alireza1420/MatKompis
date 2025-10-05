import os, json
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# Few-shot examples keep it robust but cheap
SYSTEM_PROMPT = """
You are a shopping assistant for Swedish grocery stores.
When extracting product names, use their Swedish term 
(e.g. salmon → lax, chicken → kyckling). You are a strict intent classifier. 
Return ONLY JSON like {"intent": "...", "slots": {...}}.
Intents: ["product_nutrient", "price_query", "unknown"]
Examples:
Q: What is the protein in Kycklingkebab Fryst?
A: {"intent":"product_nutrient","slots":{"product":"Kycklingkebab Fryst","nutrient":"protein"}}
Q: How much does Kyckling Lårfilé cost?
A: {"intent":"price_query","slots":{"product":"Kyckling Lårfilé"}}
Q: Hello
A: {"intent":"unknown","slots":{}}
"""

def classify(query: str) -> dict:
    resp = model.generate_content(SYSTEM_PROMPT + f"\nQ: {query}\nA:")
    try:
        data = json.loads(resp.text.strip())
    except Exception:
        data = {"intent": "unknown", "slots": {}}
    return data
