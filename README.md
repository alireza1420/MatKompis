# 🥗 MatKompis – SmartRecipe AI Assistant

**MatKompis** (“Food Buddy”) is a conversational AI assistant that provides **personalized meal recommendations** and **nutritional insights** using **real Swedish supermarket data** and **LLM-powered reasoning**.

It combines intent detection, retrieval-augmented generation (RAG), and local dataset lookups to deliver realistic and context-aware food suggestions.

---

## 🧭 Overview

The system allows users to **chat** about what they want to eat (“I want a high-protein lunch under 600 kcal”) and receive meal ideas, ingredient lists, and nutritional breakdowns — all grounded in real product data.

> 💬 *“Your AI friend for healthier, smarter, and more sustainable eating.”*

---

## 🧩 Architecture

<p align="center">
  <img width="811" height="445" alt="image" src="https://github.com/user-attachments/assets/356e599a-a5eb-438c-9910-a131a0fc7553" />
</p>

### 🔹 Flow Summary

1. **User Input** via Gradio Chat UI  
2. **FastAPI Backend** receives `/ask` requests  
3. **Gemini API (Intent Classification)** identifies query type  
   - Meal recommendation / recipe query  
   - Nutrition or price query  
4. **SentenceTransformer Models**
   - `all-MiniLM-L6-v2`: for recipe semantic matching  
   - `KBLab/sentence-bert-swedish-cased`: for Swedish text embedding  
5. **String Lookup Modules**
   - Recipe dataset lookup  
   - Product dataset lookup  
6. **Gemini API (RAG Answer Generation)** synthesizes final response  
7. **Response Displayed** in Gradio interface

---

## ⚙️ Features

- 🍽️ **Personalized Meal Recommendations**  
- 🧮 **Nutritional Estimation (kcal, protein, carbs, fat)**  
- 🛒 **Integration with ICA & Hemköp Datasets**  
- 🧠 **LLM-powered Understanding (Gemini / OpenAI)**  
- 🧾 **RAG Architecture with Sentence Embeddings**  
- 🧑‍🍳 **Local Recipe & Product Lookup**  

---

## 🚀 Getting Started

### 1️⃣ Clone the repository
```bash
git clone https://github.com/alireza1420/MatKompis.git
cd MatKompi
```
2️⃣ Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # or on Windows: venv\Scripts\activate
```
