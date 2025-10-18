import gradio as gr
import requests

API_URL = "http://127.0.0.1:8000/ask"

def ask_bot(message, history):
    # Send query to FastAPI backend
    try:
        response = requests.get(API_URL, params={"q": message})
        data = response.json()
        intent = data.get("intent", "unknown")
        answer = data.get("answer", "Sorry, something went wrong.")
        
        # Add a friendly label depending on intent
        if intent == "product_nutrient":
            prefix = "🥗 Nutrient info:"
        elif intent == "price_query":
            prefix = "💰 Price info:"
        elif intent == "recipe_query":
            prefix = "👩‍🍳 Recipe ideas:"
        else:
            prefix = "🤖"
        
        # Format recipe lists a bit prettier
        if "•" in answer:
            lines = answer.split("•")
            formatted = [f"🍽️ {l.strip()}" for l in lines if l.strip()]
            answer = "\n".join(formatted)
        
        return f"{prefix}\n{answer}"
    
    except Exception as e:
        return f"Error contacting server: {e}"

# UI Design

TITLE = "🥗 SmartRecipe Assistant 🍜"
DESCRIPTION = """
Welcome to your personal **AI-powered Food Assistant** 🧑‍🍳✨  

Ask me about **nutrients**, **prices**, or get **delicious recipe suggestions** 🍲  

💡 Try asking things like:  
- 🥦 *"What’s the protein in tofu?"*  
- 💰 *"How much does salmon cost?"*  
- 🍜 *"Can you suggest a recipe with miso?"*  
- 🌱 *"Find a high-protein vegan meal"*
"""


light_theme = gr.themes.Soft(
    primary_hue="green",
    secondary_hue="lime",
).set(
    body_background_fill="#f9faf7",        
    body_text_color="#2f2f2f",             
    background_fill_secondary="#f4f7f4",   
    border_color_primary="#dce2da",        
    button_primary_background_fill="#72b37e",
    button_primary_background_fill_hover="#5aa169",
    block_shadow="0px 2px 10px rgba(0, 0, 0, 0.05)",)

chatbot = gr.ChatInterface(
    fn=ask_bot,
    title=TITLE,
    description=DESCRIPTION,
    theme=light_theme,
    examples = [
    ["🥦 What’s the protein in tofu?"],
    ["💰 How much does Kycklingkebab Fryst cost?"],
    ["👩‍🍳 Suggest a recipe with miso"],
    ["🌱 Find a high-protein vegan meal"],
    ["🍝 Show me a vegetarian pasta idea"]],
    type="messages")

chatbot.footer = "🍴 Powered by SmartRecipe AI • Helping you cook smarter"

if __name__ == "__main__":
    chatbot.launch(server_port=None)
