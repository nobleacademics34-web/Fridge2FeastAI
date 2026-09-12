import base64
import json
import io
import streamlit as st
from PIL import Image
from pypdf import PdfReader
from pydantic import BaseModel, Field
from groq import Groq

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="Fridge2Feast AI (Groq)",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🍳 Fridge2Feast AI")
st.caption("Powered by ultra-fast Groq AI models! Upload photos, ingredients, or custom PDF cookbooks.")

# --- 2. Data Structures for Structured Output ---
class Recipe(BaseModel):
    title: str = Field(description="Name of the dish")
    cook_time: str = Field(description="Estimated preparation and cooking time (e.g., '25 mins')")
    difficulty: str = Field(description="Skill level required: Easy, Medium, or Hard")
    ingredients_used: list[str] = Field(description="Ingredients detected or provided that are used in this recipe")
    missing_pantry_items: list[str] = Field(description="Common household items needed (e.g., salt, olive oil, pepper)")
    instructions: list[str] = Field(description="Sequential step-by-step cooking directions")

class RecipeResponse(BaseModel):
    recipes: list[Recipe] = Field(description="A list of 3 distinct recipe options")

# --- Helper: Convert PIL Image to Base64 for Groq Vision ---
def encode_image_to_base64(image: Image.Image) -> str:
    buffered = io.BytesIO()
    # Convert image to RGB if RGBA
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# --- 3. Sidebar Setup ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Secure API Key handling for GROQ_API_KEY
    api_key = st.secrets.get("GROQ_API_KEY", "")
    if not api_key:
        api_key = st.text_input("Enter Groq API Key", type="password", help="Get a key from console.groq.com")
    else:
        st.success("Groq API Key loaded from secrets!", icon="🔐")

    st.divider()
    st.header("🥗 Preferences")
    dietary_pref = st.multiselect(
        "Dietary Filters",
        ["Vegetarian", "Vegan", "Gluten-Free", "High-Protein", "Keto", "Dairy-Free"]
    )
    skill_level = st.select_slider("Target Skill Level", options=["Beginner", "Intermediate", "Advanced"])

# --- 4. Main App Inputs ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Visual & Text Inputs")
    uploaded_image = st.file_uploader("📷 Upload Fridge / Food Photo", type=["jpg", "jpeg", "png"])
    image_obj = None
    if uploaded_image:
        image_obj = Image.open(uploaded_image)
        st.image(image_obj, caption="Uploaded Image", use_container_width=True)

    text_ingredients = st.text_area(
        "📝 Extra or Specific Ingredients",
        placeholder="e.g., 2 eggs, half an onion, cheddar cheese, leftover rice...",
        height=100
    )

with col2:
    st.subheader("2. Optional Knowledge Grounding")
    uploaded_pdf = st.file_uploader("📄 Upload Cookbook PDF (Optional)", type=["pdf"])
    pdf_text_context = ""
    if uploaded_pdf:
        try:
            reader = PdfReader(uploaded_pdf)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    pdf_text_context += extracted + "\n"
            st.success(f"Successfully extracted {len(reader.pages)} pages from PDF!", icon="📚")
        except Exception as e:
            st.error(f"Error reading PDF file: {e}")

# --- 5. Execution Logic ---
st.divider()

if st.button("✨ Generate 3 Custom Recipes", type="primary", use_container_width=True):
    if not api_key:
        st.error("Missing Groq API Key! Add GROQ_API_KEY to your Streamlit secrets or sidebar.")
    elif not uploaded_image and not text_ingredients.strip() and not pdf_text_context:
        st.warning("Please upload an image, enter text ingredients, or provide a PDF cookbook to start.")
    else:
        try:
            client = Groq(api_key=api_key)
            
            prompt_text = f"""
            You are an expert chef. Analyze all provided inputs (fridge images, manual ingredients list, and cookbook context).
            Generate 3 distinct, practical recipes using as many available ingredients as possible.

            User Preferences:
            - Dietary Restrictions: {', '.join(dietary_pref) if dietary_pref else 'None'}
            - Target Skill Level: {skill_level}
            - Manual Ingredient List: {text_ingredients if text_ingredients.strip() else 'None'}

            Cookbook PDF Knowledge Grounding:
            {pdf_text_context[:4000] if pdf_text_context else 'No external PDF provided. Use general culinary knowledge.'}

            Rules:
            1. Prioritize using ingredients provided or visible in the photo.
            2. If cookbook PDF text is provided, prioritize matching recipes from that text first.
            3. Return ONLY valid JSON adhering strictly to the schema without conversational text.
            """

            # Structure content payload based on vision vs text
            content_payload = []
            if image_obj:
                base64_image = encode_image_to_base64(image_obj)
                content_payload.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                })
            
            content_payload.append({"type": "text", "text": prompt_text})

            with st.spinner("Analyzing inputs & crafting recipes with Groq..."):
                # Use Groq multimodal vision model and JSON response format
                response = client.chat.completions.create(
                    model="llama-3.2-11b-vision-preview" if image_obj else "llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "user",
                            "content": content_payload
                        }
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3
                )

                raw_json = response.choices[0].message.content
                parsed_data = json.loads(raw_json)
                
                # Normalize response keys
                if "recipes" in parsed_data:
                    st.session_state['generated_recipes'] = parsed_data["recipes"]
                else:
                    st.session_state['generated_recipes'] = [parsed_data]

        except Exception as e:
            st.error(f"Failed to generate recipes with Groq: {str(e)}")

# --- 6. Render Results ---
if 'generated_recipes' in st.session_state:
    recipes = st.session_state['generated_recipes']
    st.subheader("🎉 Your Custom Recipe Options")

    tab_titles = [f"Option {idx + 1}: {r.get('title', 'Recipe')}" for idx, r in enumerate(recipes)]
    tabs = st.tabs(tab_titles)

    for idx, tab in enumerate(tabs):
        r = recipes[idx]
        with tab:
            m1, m2, m3 = st.columns(3)
            m1.metric("⏱ Prep/Cook Time", r.get('cook_time', 'N/A'))
            m2.metric("📊 Difficulty", r.get('difficulty', 'N/A'))
            m3.metric("🛒 Main Ingredients", len(r.get('ingredients_used', [])))

            st.divider()
            col_a, col_b = st.columns([1, 2])

            with col_a:
                st.write("### 🥦 Ingredients Used")
                for ing in r.get('ingredients_used', []):
                    st.markdown(f"- {ing}")

                if r.get('missing_pantry_items'):
                    st.write("### 🧂 Pantry Items Needed")
                    for pantry_item in r['missing_pantry_items']:
                        st.caption(f"• {pantry_item}")

            with col_b:
                st.write("### 📖 Step-by-Step Instructions")
                for step_num, step in enumerate(r.get('instructions', []), 1):
                    st.write(f"**{step_num}.** {step}")
