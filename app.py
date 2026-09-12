import base64
import json
import io
import streamlit as st
from PIL import Image
from pypdf import PdfReader
from pydantic import BaseModel, Field
from groq import Groq

# --- 1. Page Config & CSS for Custom Background and Chat Colors ---
st.set_page_config(
    page_title="Fridge2Feast AI",
    page_icon="🍳",
    layout="wide"
)

# Custom CSS injected into Streamlit
st.html("""
    <style>
    /* 1. App Main Canvas Background (Soft Cream) */
    .stAppViewContainer {
        background-color: #FAF8F5 !important;
    }

    /* Page container limits */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 5rem !important;
        max-width: 900px !important;
    }
    
    /* 2. Target User Chat Messages (Right-aligned, Warm Sage/Mint Accent) */
    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from user"]) {
        flex-direction: row-reverse !important;
        background-color: #D8E2DC !important;
        color: #1F2421 !important;
        border: 1px solid #C4D3CB !important;
        border-radius: 18px 18px 2px 18px !important;
        margin-left: auto !important;
        max-width: 80% !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03) !important;
    }
    
    /* 3. Target Assistant Chat Messages (Left-aligned, Crisp Card White) */
    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from assistant"]) {
        background-color: #FFFFFF !important;
        color: #2D3142 !important;
        border: 1px solid #EAE6DF !important;
        border-radius: 18px 18px 18px 2px !important;
        margin-right: auto !important;
        max-width: 85% !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03) !important;
    }
    
    /* Image Preview Styling inside Chat */
    div[data-testid="stChatMessage"] img {
        border-radius: 10px;
    }
    </style>
""")

st.title("🍳 Fridge2Feast AI")
st.caption("Chat with your AI Chef! Type your ingredients, upload a fridge photo, or drop a cookbook PDF in the sidebar.")

# --- 2. Pydantic Schema ---
class Recipe(BaseModel):
    title: str = Field(description="Name of the dish")
    cook_time: str = Field(description="Estimated preparation and cooking time (e.g., '25 mins')")
    difficulty: str = Field(description="Skill level required: Easy, Medium, or Hard")
    ingredients_used: list[str] = Field(description="Ingredients detected or provided that are used in this recipe")
    missing_pantry_items: list[str] = Field(description="Common household items needed (e.g., salt, olive oil)")
    instructions: list[str] = Field(description="Sequential step-by-step cooking directions")

# Helper function: Convert image to Base64 for Groq Vision
def encode_image_to_base64(image: Image.Image) -> str:
    buffered = io.BytesIO()
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# --- 3. Sidebar (Preferences & Grounding PDF) ---
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

# --- 4. Session State Chat History ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant", 
            "content": "Hello! What ingredients do you have today? You can type them out or attach a photo of your fridge!"
        }
    ]

# Display past messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if "image" in msg and msg["image"]:
            st.image(msg["image"], width=260)
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

# --- 5. Unified Chat Input ---
uploaded_photo = st.file_uploader("📷 Optional: Attach fridge photo before sending", type=["jpg", "jpeg", "png"], key="chat_photo")
user_input = st.chat_input("Ask for a recipe or type your ingredients...")

if user_input or uploaded_photo:
    if not api_key:
        st.error("Please add your Groq API key in secrets or sidebar.")
    else:
        # Prepare User UI display
        img_obj = Image.open(uploaded_photo) if uploaded_photo else None
        user_msg = {"role": "user", "content": user_input if user_input else "What can I cook with these ingredients?", "image": img_obj}
        st.session_state.messages.append(user_msg)
        
        with st.chat_message("user"):
            if img_obj:
                st.image(img_obj, width=260)
            if user_input:
                st.markdown(user_input)

        # Generate Response from Groq
        with st.chat_message("assistant"):
            with st.spinner("Chef AI is cooking up recipes..."):
                try:
                    client = Groq(api_key=api_key)
                    
                    prompt_text = f"""
                    You are an expert chef. Analyze the user request, image (if provided), and cookbook context.
                    Generate 3 distinct recipes.
                    
                    User Message: {user_input}
                    Dietary Restrictions: {', '.join(dietary_pref) if dietary_pref else 'None'}
                    Skill Level: {skill_level}
                    Cookbook Text Context: {pdf_text_context[:4000] if pdf_text_context else 'None'}
                    
                    Return ONLY valid JSON with this format:
                    {{
                        "recipes": [
                            {{
                                "title": "Recipe Name",
                                "cook_time": "20 mins",
                                "difficulty": "Easy",
                                "ingredients_used": ["Item 1", "Item 2"],
                                "missing_pantry_items": ["Salt"],
                                "instructions": ["Step 1...", "Step 2..."]
                            }}
                        ]
                    }}
                    """

                    content_payload = []
                    if img_obj:
                        base64_image = encode_image_to_base64(img_obj)
                        content_payload.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        })
                    content_payload.append({"type": "text", "text": prompt_text})

                    response = client.chat.completions.create(
                        model="llama-3.2-90b-vision-preview" if img_obj else "llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": content_payload}],
                        response_format={"type": "json_object"},
                        temperature=0.3
                    )

                    raw_json = response.choices[0].message.content
                    parsed_data = json.loads(raw_json)
                    recipes_data = parsed_data.get("recipes", [parsed_data])

                    assistant_text = "Here are 3 custom recipes I created for you based on your request:"
                    st.markdown(assistant_text)

                    # Display formatted tabs
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

                    # Save to state
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_text,
                        "recipes": recipes_data
                    })

                except Exception as e:
                    st.error(f"Error generating recipes: {e}")
