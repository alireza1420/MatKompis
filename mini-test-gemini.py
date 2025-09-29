import os
import pandas as pd
import gradio as gr
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
import google.generativeai as genai

# for google-generativeai, please run "pip install -U google-generativeai"

# Configure API key
GOOGLE_API_KEY = "your_google_api_key_here"
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
genai.configure(api_key=GOOGLE_API_KEY)

# File paths
ICA_CSV_PATH = "ica-scrapping/ica_category_data/ica_meat_data.csv"
RECIPE_CSV_PATH = "recipe_data.csv"

def load_and_process_data(ica_path, recipe_path):
    """Load and process ICA nutrition data and recipe data"""
    documents = []
    
    # Process ICA data
    try:
        if os.path.exists(ica_path):
            print(f"Loading ICA data from {ica_path}")
            ica_df = pd.read_csv(ica_path).head(100)
            
            for _, row in ica_df.iterrows():
                content = f"""
                Product: {row.get('Name', 'Unknown')}
                Price: {row.get('Price', 'N/A')}
                Size: {row.get('Size', 'N/A')}
                Energy: {row.get('Energi (kcal)', 0)} kcal per 100g
                Fat: {row.get('Fett', 0)} g per 100g
                Carbohydrates: {row.get('Kolhydrat', 0)} g per 100g
                Protein: {row.get('Protein', 0)} g per 100g
                Category: Meat
                """
                documents.append(Document(
                    page_content=content,
                    metadata={
                        "source": "ica_meat",
                        "product_name": row.get('Name', 'Unknown'),
                        "protein_per_100g": row.get('Protein', 0),
                        "calories_per_100g": row.get('Energi (kcal)', 0),
                        "url": row.get('url', '')
                    }
                ))
            print(f"Loaded {len(ica_df)} ICA products")
    except Exception as e:
        print(f"Error loading ICA data: {e}")
    
    # Process recipe data
    try:
        if os.path.exists(recipe_path):
            print(f"Loading recipe data from {recipe_path}")
            recipe_df = pd.read_csv(recipe_path).head(100)
            
            for _, row in recipe_df.iterrows():
                title = row.get('Title', 'Unknown Recipe')
                instructions = row.get('Instructions', 'Not specified')
                cleaned_ingredients = row.get('Cleaned_Ingredients', 'Not specified')
                
                content = f"""
                Recipe: {title}
                Ingredients: {cleaned_ingredients}
                Instructions: {instructions}
                """
                documents.append(Document(
                    page_content=content,
                    metadata={
                        "source": "recipe",
                        "recipe_title": title,
                        "cleaned_ingredients": cleaned_ingredients
                    }
                ))
            print(f"Loaded {len(recipe_df)} recipes")
    except Exception as e:
        print(f"Error loading recipe data: {e}")
    
    return documents

def setup_vectorstore(documents):
    """Setup vector store with documents"""
    try:
        # Initialize embeddings
        embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        print("Embeddings initialized")
        
        # Split documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        splits = text_splitter.split_documents(documents)
        print(f"Creating vector store with {len(splits)} document chunks...")
        
        # Create Chroma vector store
        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory="./chroma_db"
        )
        print("Vector store created successfully")
        return vectorstore
        
    except Exception as e:
        print(f"Vector store setup failed: {e}")
        raise e

def generate_recipe(user_query):
    """Generate recipe based on user query"""
    if not vectorstore:
        return "Error: Vector store not initialized!"
    
    try:
        # Retrieve relevant documents
        relevant_docs = vectorstore.similarity_search(user_query, k=3)
        context = "\n".join([doc.page_content for doc in relevant_docs])
        
        # Generate with Gemini
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""
Based on the following nutrition and recipe information, answer the user's question about creating a recipe.

Context:
{context}

User Question: {user_query}

Provide a detailed recipe including:
1. Ingredient list with quantities
2. Step-by-step instructions
3. Estimated nutritional content (protein, calories, carbs, fat)
4. Prep and cook time

Use ingredients from the provided context when possible.
"""
        
        response = model.generate_content(prompt)
        
        # Add sources
        result = response.text + "\n\n--- Sources Used ---\n"
        for doc in relevant_docs:
            if doc.metadata.get('source') == 'ica_meat':
                product_name = doc.metadata.get('product_name', 'Unknown')
                protein = doc.metadata.get('protein_per_100g', 'N/A')
                calories = doc.metadata.get('calories_per_100g', 'N/A')
                url = doc.metadata.get('url', '')
                result += f"• ICA Product: {product_name} ({protein}g protein, {calories} kcal per 100g)\n"
                if url:
                    result += f"  Link: {url}\n"
            elif doc.metadata.get('source') == 'recipe':
                recipe_title = doc.metadata.get('recipe_title', 'Unknown')
                result += f"• Recipe Reference: {recipe_title}\n"
        
        return result
        
    except Exception as e:
        return f"Error generating recipe: {str(e)}"

# Initialize data and vector store on startup
print("Initializing chatbot...")
documents = load_and_process_data(ICA_CSV_PATH, RECIPE_CSV_PATH)
vectorstore = setup_vectorstore(documents)
print("Chatbot ready!")

# Gradio interface
def create_interface():
    with gr.Blocks(title="Recipe Nutrition Chatbot") as demo:
        gr.Markdown("# 🍳 Recipe Nutrition Chatbot")
        gr.Markdown("Ask for recipes based on nutritional requirements!")
        
        with gr.Row():
            with gr.Column():
                user_input = gr.Textbox(
                    label="Ask for a recipe",
                    placeholder="e.g., 'Give me a recipe with 30g protein' or 'I need a low-carb high-protein meal'",
                    lines=3
                )
                submit_btn = gr.Button("Generate Recipe", variant="primary")
                
            with gr.Column():
                output = gr.Textbox(
                    label="Generated Recipe",
                    lines=20,
                    interactive=False
                )
        
        # Event handlers
        submit_btn.click(fn=generate_recipe, inputs=user_input, outputs=output)
        user_input.submit(fn=generate_recipe, inputs=user_input, outputs=output)
        
        # Example queries
        gr.Markdown("### Example Queries:")
        examples = [
            "Give me a high protein recipe with at least 30g protein using meat",
            "I need a low-carb meal under 10g carbs",
            "Create a recipe with chicken",
            "What's a good post-workout meal?",
        ]
        for example in examples:
            gr.Markdown(f"- *{example}*")
    
    return demo

if __name__ == "__main__":
    demo = create_interface()
    demo.launch(share=True, debug=True)