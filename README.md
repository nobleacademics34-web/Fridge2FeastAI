# 🍳 Fridge2Feast AI (Groq Edition)

Fridge2Feast AI is an interactive web application that converts leftover ingredients into tailored recipes using **Groq AI** models and **Streamlit**.

## ✨ Key Features
- **Visual Food Detection:** Upload a photo of your open fridge or food pantry to automatically identify items.
- **Ultra-Fast Inference:** Powered by Groq's high-speed Llama models.
- **RAG Knowledge Grounding:** Upload custom PDF cookbooks to prioritize specific recipes.

---

## 🌐 Deploy to Streamlit Community Cloud

1. Push your repository to **GitHub**.
2. Visit [share.streamlit.io](https://share.streamlit.io) and select your repository (`app.py`).
3. Under **Advanced Settings > Secrets**, paste:
   ```toml
   GROQ_API_KEY = "gsk_your_groq_api_key_here"
