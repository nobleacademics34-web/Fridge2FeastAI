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

# --- 2. Custom CSS (Theme: Warm Beige & Integrated Pin Icon inside Chat Bar) ---
st.html("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Background Canvas with Animated Kitchen Doodles */
    .stAppViewContainer {
        background-color: #F5EFEB !important;
        background-image: url("data:image/svg+xml,%3Csvg width='80' height='80' viewBox='0 0 80 80' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%23A06C52' fill-opacity='0.08'%3E%3Cpath d='M10 15a3 3 0 1 1 6 0 3 3 0 0 1-6 0zm35 5a2 2 0 1 0 0-4 2 2 0 0 0 0 4zm20-10a4 4 0 1 1 8 0 4 4 0 0 1-8 0zM15 50a2 2 0 1 0 0-4 2 2 0 0 0 0 4zm40 10a3 3 0 1 1 6 0 3 3 0 0 1-6 0zm-20 5a2 2 0 1 0 0-4 2 2 0 0 0 0 4z'/%3E%3Cpath d='M30 25c2 0 3-1 3-3s-1-3-3-3-3 1-3 3 1 3 3 3zm25 20c2.5 0 4-1.5 4-4s-1.5-4-4-4-4 1.5-4 4 1.5 4 4 4zM10 70c2 0 3-1 3-3s-1-3-3-3-3 1-3 3 1 3 3 3z'/%3E%3C/g%3E%3C/svg%3E");
        animation: floatingDoodles 60s linear infinite;
    }

    @keyframes floatingDoodles {
        0% { background-position: 0 0; }
        100% { background-position: 500px 500px; }
    }

    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 7rem !important;
        max-width: 880px !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #EDE3DA !important;
        border-right: 1px solid #E2D5C7 !important;
    }

    /* User Chat Message Styling */
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

    /* Assistant Chat Message Styling */
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

    /* --- INTEGRATED PIN ICON INSIDE SEARCH BAR --- */
    div[data-testid="stColumn"]:has(div[data-testid="stFileUploader"]) {
        position: relative !important;
        z-index: 999 !important;
    }

    div[data-testid="stChatInput"] {
        position: relative !important;
    }

    div[data-testid="stChatInput"] textarea {
        padding-left: 48px !important;
    }

    div[data-testid="stFileUploader"] {
        position: absolute !important;
        left: 12px !important;
        bottom: 8px !important;
        z-index: 1000 !important;
        width: 36px !important;
        min-width: 36px !important;
        height: 36px !important;
    }

    div[data-testid="stFileUploader"] section {
        padding: 0 !important;
        background: transparent !important;
        border: none !important;
        height: 36px !important;
        width: 36px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: pointer !important;
    }

    div[data-testid="stFileUploader"] section:hover {
        background: rgba(217, 119, 69, 0.1) !important;
        border-radius: 50% !important;
    }

    div[data-testid="stFileUploader"] section span, 
    div[data-testid="stFileUploader"] section small, 
    div[data-testid="stFileUploader"] section div {
        display: none !important;
    }

    div[data-testid="stFileUploader"] section::after {
        content: "📌";
        font-size: 18px;
        display: block;
    }

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
st.caption("Your culinary companion! Type your ingredients or click the pin icon inside the chat bar to upload a photo.")

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

def get_active_groq_model(client: Groq, vision_required: bool = False) -> str:
    """Dynamically queries available models to prevent 404/decommission errors."""
    try:
        available_models = [m.id for m in client.models.list().data]
        if vision_required:
            vision_models = [m for m in available_models if "vision" in m.lower()]
            if vision_models:
                return vision_models[0]
            return "llama-3.2-11b-vision-instruct"
        else:
            text_models = [m for m in available_models if "llama" in m.lower() and "vision" not in m.lower()]
            if text_models:
                return text_models[0]
            return "llama-3.1-70b-versatile"
    except Exception:
        return "llama-3.2-11b-vision-instruct" if vision_required else "llama-3.1-70b-versatile"

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

# --- 5. Session State & Chat History ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant", 
            "content": "Hello! What ingredients do you have today? Type them below or click the pin icon inside the input bar to attach a photo!"
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

# --- 6. Input Section ---
col_upload, col_input = st.columns([0.01, 0.99])
with col_upload:
    uploaded_photo = st.file_uploader("", type=["jpg", "jpeg", "png"], key="chat_photo", label_visibility="collapsed")
with col_input:
    user_input = st.chat_input("Ask for a recipe or list your ingredients...")

if user_input or uploaded_photo:
    if not api_key:
        st.error("Please add your Groq API key in secrets or sidebar.")
    else:
        img_obj = Image.open(uploaded_photo) if uploaded_photo else None
        input_text = user_input if user_input else "What recipes can I make with these ingredients?"
        
        user_msg = {"role": "user", "content": input_text, "image": img_obj}
        st.session_state.messages.append(user_msg)
        
        with st.chat_message("user"):
            if img_obj:
                st.image(img_obj, width=240)
            st.markdown(input_text)

        with st.chat_message("assistant"):
            with st.spinner("Chef AI is cooking up recipes..."):
                try:
                    client = Groq(api_key=api_key)
                    
                    prompt_text = (
                        f"You are an expert chef. Analyze the request, optional image, and cookbook context.\n"
                        f"Generate 3 distinct recipes.\n\n"
                        f"User Request: {input_text}\n"
                        f"Dietary Restrictions: {', '.join(dietary_pref) if dietary_pref else 'None'}\n"
                        f"Skill Level: {skill_level}\n"
                        f"Cookbook Context: {pdf_text_context[:3000] if pdf_text_context else 'None'}\n\n"
                        f"Return ONLY valid JSON with structure:\n"
                        f'{{\n  "recipes": [\n    {{\n'
                        f'      "title": "Recipe Name",\n'
                        f'      "cook_time": "20 mins",\n'
                        f'      "difficulty": "Easy",\n'
                        f'      "ingredients_used": ["Item 1"],\n'
                        f'      "missing_pantry_items": ["Salt"],\n'
                        f'      "instructions": ["Step 1..."]\n'
                        f'    }}\n  ]\n}}'
                    )

                    # Dynamic Resolution of Active Groq Model Endpoint
                    selected_model = get_active_groq_model(client, vision_required=bool(img_obj))

                    if img_obj:
                        base64_image = encode_image_to_base64(img_obj)
                        content_payload = [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                            },
                            {
                                "type": "text",
                                "text": prompt_text
                            }
                        ]
                    else:
                        content_payload = prompt_text

                    response = client.chat.completions.create(
                        model=selected_model,
                        messages=[{"role": "user", "content": content_payload}],
                        response_format={"type": "json_object"},
                        temperature=0.3
                    )

                    raw_json = response.choices[0].message.content
                    parsed_data = json.loads(raw_json)
                    recipes_data = parsed_data.get("recipes", [parsed_data])

                    assistant_text = "Here are 3 custom recipes I created for you based on your request:"
                    st.markdown(assistant_text)

                    tabs = st.tabs([f"Option {i+1}: {r.get('title', 'Recipe')}" for i, r in enumerate(recipes_data)])
                    for idx, tab in enumerate(tabs):
                        r = recipes_data[idx]
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

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_text,
                        "recipes": recipes_data
                    })

                except Exception as e:
                    st.error(f"Error generating recipes: {e}")
