import base64
import json
import io
import streamlit as st
from PIL import Image
from pypdf import PdfReader
from pydantic import BaseModel, Field
from groq import Groq

# --- 1. Page Config ---
st.set_page_config(
    page_title="Fridge2Feast AI",
    page_icon="🍳",
    layout="wide"
)

# --- 2. Custom CSS (Theme: Warm Beige & Animated Kitchen Doodles) ---
st.html("""
    <style>
    /* Google Font Import */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* 1. Background Canvas with Subtle Animated Kitchen Doodles */
    .stAppViewContainer {
        background-color: #F5EFEB !important;
        background-image: url("data:image/svg+xml,%3Csvg width='80' height='80' viewBox='0 0 80 80' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%23A06C52' fill-opacity='0.08'%3E%3Cpath d='M10 15a3 3 0 1 1 6 0 3 3 0 0 1-6 0zm35 5a2 2 0 1 0 0-4 2 2 0 0 0 0 4zm20-10a4 4 0 1 1 8 0 4 4 0 0 1-8 0zM15 50a2 2 0 1 0 0-4 2 2 0 0 0 0 4zm40 10a3 3 0 1 1 6 0 3 3 0 0 1-6 0zm-20 5a2 2 0 1 0 0-4 2 2 0 0 0 0 4z'/%3E%3Cpath d='M30 25c2 0 3-1 3-3s-1-3-3-3-3 1-3 3 1 3 3 3zm25 20c2.5 0 4-1.5 4-4s-1.5-4-4-4-4 1.5-4 4 1.5 4 4 4zM10 70c2 0 3-1 3-3s-1-3-3-3-3 1-3 3 1 3 3 3z'/%3E%3C/g%3E%3C/svg%3E");
        animation: floatingDoodles 60s linear infinite;
    }

    @keyframes floatingDoodles {
        0% { background-position: 0 0; }
        100% { background-position: 500px 500px; }
    }

    /* Page container bounds */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 7rem !important;
        max-width: 880px !important;
    }

    /* 2. Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #EDE3DA !important;
        border-right: 1px solid #E2D5C7 !important;
    }

    /* 3. User Chat Bubble (Terracotta Accent) */
    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from user"]) {
        flex-direction: row-reverse !important;
        background: linear-gradient(135deg, #D97745 0%, #C86D3B 100%) !important;
        color: #FFFFFF !important;
        border-radius: 20px 20px 4px 20px !important;
        margin-left: auto !important;
        max-width: 80% !important;
        box-shadow: 0 4px 12px rgba(217, 119, 69, 0.15) !important;
        transition: transform 0.2s ease;
    }
    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from user"]):hover {
        transform: translateY(-2px);
    }

    /* 4. Assistant Chat Bubble (Soft Cream Card) */
    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from assistant"]) {
        background-color: #FFFFFF !important;
        color: #2D2522 !important;
        border: 1px solid #E8DEC8 !important;
        border-radius: 20px 20px 20px 4px !important;
        margin-right: auto !important;
        max-width: 85% !important;
        box-shadow: 0 4px 15px rgba(160, 108, 82, 0.06) !important;
        transition: transform 0.2s ease;
    }
    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from assistant"]):hover {
        transform: translateY(-2px);
    }

    /* 5. Custom Upload + Chat Input Container */
    .chat-input-wrapper {
        background-color: #FFFFFF;
        border: 1.5px solid #E8DEC8;
        border-radius: 16px;
        padding: 8px 12px;
        box-shadow: 0 4px 20px rgba(160, 108, 82, 0.08);
        transition: border-color 0.2s ease;
    }
    .chat-input-wrapper:focus-within {
        border-color: #D97745;
    }

    /* Hide standard borders on nested Streamlit widgets inside our bar */
    div[data-testid="stFileUploader"] {
        padding: 0 !important;
    }
    div[data-testid="stFileUploader"] section {
        padding: 4px 8px !important;
        background: #F8F4EE !important;
        border: 1px dashed #D3C4B3 !important;
        border-radius: 10px !important;
    }

    /* Tab styling override */
    button[data-baseweb="tab"] {
        color: #7A6258 !important;
    }
    button[aria-selected="true"] {
        color: #C86D3B !important;
        border-bottom-color: #C86D3B !important;
        font-weight: bold !important;
    }
    </style>
""")

st.title("🍳 Fridge2Feast AI")
st.caption("Your culinary companion! Type your ingredients or attach a photo right in the input bar.")

# --- 3. Schema & Helpers ---
class Recipe(BaseModel):
    title: str = Field(description="Name of the dish")
    cook_time: str = Field(description="Estimated preparation and cooking time")
    difficulty: str = Field(description="Skill level required: Easy, Medium, or Hard")
    ingredients_used: list[str] = Field(description="Ingredients used")
    missing_pantry_items: list[str] = Field(description="Common pantry staples needed")
    instructions: list[str] = Field(description="Sequential cooking steps")

def encode_image_to_base64(image: Image.Image) -> str:
    buffered = io.BytesIO()
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# --- 4. Sidebar ---
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.secrets.get("GROQ_API_KEY", "")
    if not api_key:
        api_key = st.text_input("Enter Groq API Key", type="password")
    else:
        st.success("Groq Key Loaded", icon="🔐")

    st.divider()
    st.header("🥗 Preferences")
    dietary_pref = st.multiselect("Dietary Filters", ["Vegetarian", "Vegan", "Gluten-Free", "High-Protein", "Keto"])
    skill_level = st.select_slider("Skill Level", options=["Beginner", "Intermediate", "Advanced"])

    st.divider()
    st.header("📄 Grounding PDF")
    uploaded_pdf = st.file_uploader("Upload Cookbook PDF", type=["pdf"])
    pdf_text_context = ""
    if uploaded_pdf:
        try:
            reader = PdfReader(uploaded_pdf)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    pdf_text_context += extracted + "\n"
            st.success(f"Loaded {len(reader.pages)} PDF pages!")
        except Exception as e:
            st.error(f"Error reading PDF: {e}")

# --- 5. Chat History Render ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant", 
            "content": "Hello! What ingredients do you have today? Type them below or attach a photo!"
        }
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if "image" in msg and msg["image"]:
            st.image(msg["image"], width=240)
        st.markdown(msg["content"])
        if "recipes" in msg:
            tabs = st.tabs([f"Option {i+1}: {r.get('title', 'Recipe')}" for i, r in enumerate(msg["recipes"])])
            for idx, tab in enumerate(tabs):
                r = msg["recipes"][idx]
                with tab:
                    m1, m2, m3 = st.columns(3)
                    m1.metric("⏱ Cook Time", r.get("cook_time", "N/A"))
                    m2.metric("📊 Difficulty", r.get("difficulty", "N/A"))
                    m3.metric("🛒 Ingredients", len(r.get("ingredients_used", [])))
                    
                    col_a, col_b = st.columns([1, 2])
                    with col_a:
                        st.write("##### 🥦 Used Ingredients")
                        for ing in r.get("ingredients_used", []):
                            st.write(f"- {ing}")
                        if r.get("missing_pantry_items"):
                            st.write("##### 🧂 Pantry Items")
                            for p in r.get("missing_pantry_items", []):
                                st.caption(f"• {p}")
                    with col_b:
                        st.write("##### 📖 Steps")
                        for step_num, s in enumerate(r.get("instructions", []), 1):
                            st.write(f"**{step_num}.** {s}")

# --- 6. Integrated Bar (Upload Photo + Chat Input) ---
# To keep attachment close to input, we combine an upload widget alongside the chat input.
with st.container():
    col_upload, col_input = st.columns([1, 4])
    
    with col_upload:
        uploaded_photo = st.file_uploader("📷 Photo", type=["jpg", "jpeg", "png"], key="inline_photo", label_visibility="collapsed")
    
    with col_input:
        user_input = st.chat_input("Ask for a recipe or list your ingredients...")

if user_input or uploaded_photo:
    if not api_key:
        st.error("Please add your Groq API key in secrets or sidebar.")
    else:
        img_obj = Image.open(uploaded_photo) if uploaded_photo else None
        
        # Avoid running empty prompt if only photo uploaded without text
        prompt_text_user = user_input if user_input else "What recipes can I make with these ingredients?"
        
        user_msg = {"role": "user", "content": prompt_text_user, "image": img_obj}
        st.session_state.messages.append(user_msg)
        
        st.rerun()
