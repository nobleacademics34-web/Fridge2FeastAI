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

# =========================================================================
# COLOR PALETTE — "Warm Kitchen" theme
# -------------------------------------------------------------------------
#  Token                  Hex        Used for
#  --bg-beige             #F2E8D5    Main app background (warm beige)
#  --doodle-brown         #B98B56    Kitchen doodle charms in the bg pattern
#  --sidebar-bg           #EADBBD    Sidebar background (deeper beige)
#  --card-cream           #FFFBF3    Assistant chat bubble background
#  --card-border          #E3D3B8    Assistant bubble / card border
#  --user-bubble          #E7B978    User chat bubble background (caramel)
#  --user-bubble-border   #CB8F49    User chat bubble border
#  --text-dark            #4A3222    Headings / primary text
#  --text-body            #5A4632    Body text inside bubbles
#  --accent-cinnamon      #A85C32    Buttons, links, spinner, metric labels
#  --accent-sage          #8CA06A    Secondary accent (success states, tags)
#  --shadow               rgba(74,50,34,0.10)  Soft drop shadows
# =========================================================================

DOODLE_B64 = "PHN2ZyB4bWxucz0naHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmcnIHdpZHRoPScyMjAnIGhlaWdodD0nMjIwJyB2aWV3Qm94PScwIDAgMjIwIDIyMCc+CiAgPGcgZmlsbD0nbm9uZScgc3Ryb2tlPScjQjk4QjU2JyBzdHJva2Utd2lkdGg9JzMnIHN0cm9rZS1saW5lY2FwPSdyb3VuZCcgc3Ryb2tlLWxpbmVqb2luPSdyb3VuZCcgb3BhY2l0eT0nMC41NSc+CiAgICA8cmVjdCB4PScxNScgeT0nMzAnIHdpZHRoPSczMCcgaGVpZ2h0PScyNCcgcng9JzQnLz4KICAgIDxwYXRoIGQ9J000NSAzNCBxMTIgMCAxMiAxMCBxMCAxMCAtMTIgMTAnLz4KICAgIDxwYXRoIGQ9J00yMiAyMiBxMyAtNiAwIC0xMCcvPgogICAgPHBhdGggZD0nTTMyIDIyIHEzIC02IDAgLTEwJy8+CiAgICA8cGF0aCBkPSdNMTIwIDE4IHEyMCAxMCAyMCAzMCBxLTIwIC0yIC0yMCAtMzAgeicvPgogICAgPGxpbmUgeDE9JzEyMCcgeTE9JzE4JyB4Mj0nMTMyJyB5Mj0nNDUnLz4KICAgIDxsaW5lIHgxPScxNzAnIHkxPScxOCcgeDI9JzE3MCcgeTI9JzQ1Jy8+CiAgICA8cGF0aCBkPSdNMTcwIDQ1IHEtMTAgMTUgLTIgMzAnLz4KICAgIDxwYXRoIGQ9J00xNzAgNDUgcTAgMTggMCAzMCcvPgogICAgPHBhdGggZD0nTTE3MCA0NSBxMTAgMTUgMiAzMCcvPgogICAgPGVsbGlwc2UgY3g9JzQwJyBjeT0nMTE1JyByeD0nMTAnIHJ5PScxNCcvPgogICAgPGxpbmUgeDE9JzQwJyB5MT0nMTI5JyB4Mj0nNDAnIHkyPScxNjUnLz4KICAgIDxwYXRoIGQ9J00xMTAgMTM1IHEzMCA1IDI1IDM1IHEtMjUgMTAgLTM1IC0xNSBxLTUgLTE4IDEwIC0yMCB6Jy8+CiAgICA8cGF0aCBkPSdNMTA4IDEzMyBxLTQgLTggNCAtMTInLz4KICAgIDxjaXJjbGUgY3g9JzE4NScgY3k9JzEyMCcgcj0nMycvPgogICAgPGNpcmNsZSBjeD0nMTk1JyBjeT0nMTc1JyByPScyJy8+CiAgICA8Y2lyY2xlIGN4PSc2MCcgY3k9JzE4NScgcj0nMicvPgogICAgPGNpcmNsZSBjeD0nNzUnIGN5PSc2MCcgcj0nMicvPgogIDwvZz4KPC9zdmc+Cg=="

st.html(f"""
    <style>
    :root {{
        --bg-beige: #F2E8D5;
        --sidebar-bg: #EADBBD;
        --card-cream: #FFFBF3;
        --card-border: #E3D3B8;
        --user-bubble: #E7B978;
        --user-bubble-border: #CB8F49;
        --text-dark: #4A3222;
        --text-body: #5A4632;
        --accent-cinnamon: #A85C32;
        --accent-sage: #8CA06A;
        --shadow: rgba(74,50,34,0.10);
    }}

    @keyframes driftDoodles {{
        from {{ background-position: 0 0; }}
        to   {{ background-position: 220px 220px; }}
    }}
    .stAppViewContainer, [data-testid="stAppViewContainer"] {{
        background-color: var(--bg-beige) !important;
        background-image: url("data:image/svg+xml;base64,{DOODLE_B64}") !important;
        background-repeat: repeat !important;
        background-size: 220px 220px !important;
        animation: driftDoodles 50s linear infinite !important;
    }}

    .block-container {{
        padding-top: 1.5rem !important;
        padding-bottom: 6.5rem !important;
        max-width: 900px !important;
    }}

    section[data-testid="stSidebar"] {{
        background-color: var(--sidebar-bg) !important;
        border-right: 1px solid var(--card-border);
    }}
    section[data-testid="stSidebar"] * {{
        color: var(--text-dark) !important;
    }}

    @keyframes bounceEmoji {{
        0%, 100% {{ transform: translateY(0) rotate(0deg); }}
        50%      {{ transform: translateY(-6px) rotate(-8deg); }}
    }}
    .f2f-title {{
        font-size: 2.1rem;
        font-weight: 800;
        color: var(--text-dark);
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.1rem;
    }}
    .f2f-title span.icon {{
        display: inline-block;
        animation: bounceEmoji 2.4s ease-in-out infinite;
    }}
    .f2f-caption {{
        color: var(--text-body);
        opacity: 0.85;
        margin-bottom: 1rem;
    }}

    @keyframes fadeSlideIn {{
        from {{ opacity: 0; transform: translateY(14px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
    }}
    div[data-testid="stChatMessage"] {{
        animation: fadeSlideIn 0.45s ease-out;
        transition: transform 0.2s ease;
    }}
    div[data-testid="stChatMessage"]:hover {{
        transform: translateY(-1px);
    }}

    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from user"]) {{
        flex-direction: row-reverse !important;
        background-color: var(--user-bubble) !important;
        color: var(--text-dark) !important;
        border: 1px solid var(--user-bubble-border) !important;
        border-radius: 18px 18px 2px 18px !important;
        margin-left: auto !important;
        max-width: 80% !important;
        box-shadow: 0 3px 10px var(--shadow) !important;
    }}
    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from user"]) * {{
        color: var(--text-dark) !important;
    }}

    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from assistant"]) {{
        background-color: var(--card-cream) !important;
        color: var(--text-body) !important;
        border: 1px solid var(--card-border) !important;
        border-radius: 18px 18px 18px 2px !important;
        margin-right: auto !important;
        max-width: 85% !important;
        box-shadow: 0 3px 10px var(--shadow) !important;
    }}
    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from assistant"]) * {{
        color: var(--text-body) !important;
    }}

    div[data-testid="stChatMessage"] img {{
        border-radius: 10px;
    }}

    [data-testid="stChatInput"] {{
        background-color: var(--card-cream) !important;
        border: 1.5px solid var(--card-border) !important;
        border-radius: 26px !important;
        box-shadow: 0 4px 14px var(--shadow) !important;
        transition: box-shadow 0.25s ease, border-color 0.25s ease;
    }}
    [data-testid="stChatInput"]:focus-within {{
        border-color: var(--accent-cinnamon) !important;
        box-shadow: 0 0 0 3px rgba(168,92,50,0.18) !important;
    }}
    [data-testid="stChatInput"] textarea {{
        color: var(--text-dark) !important;
    }}
    [data-testid="stChatInputSubmitButton"] button,
    [data-testid="stChatInput"] button {{
        color: var(--accent-cinnamon) !important;
    }}

    .stButton button, .stDownloadButton button {{
        background-color: var(--accent-cinnamon) !important;
        color: #FFFBF3 !important;
        border-radius: 12px !important;
        border: none !important;
    }}
    button[data-baseweb="tab"] {{
        color: var(--text-body) !important;
    }}
    button[aria-selected="true"][data-baseweb="tab"] {{
        color: var(--accent-cinnamon) !important;
        border-bottom-color: var(--accent-cinnamon) !important;
    }}
    div[data-testid="stMetric"] {{
        background-color: var(--card-cream);
        border: 1px solid var(--card-border);
        border-radius: 12px;
        padding: 0.6rem;
    }}
    div[data-testid="stMetricLabel"] {{
        color: var(--accent-cinnamon) !important;
    }}
    div[data-testid="stMetricValue"] {{
        color: var(--text-dark) !important;
    }}

    div[data-testid="stSpinner"] div {{
        border-top-color: var(--accent-cinnamon) !important;
    }}
    div[data-testid="stSpinner"] p {{
        color: var(--text-dark) !important;
    }}

    div[data-testid="stAlertContentSuccess"] {{
        background-color: rgba(140,160,106,0.18) !important;
    }}
    </style>
""")

st.markdown(
    """
    <div class="f2f-title"><span class="icon">🍳</span> Fridge2Feast AI</div>
    <div class="f2f-caption">Chat with your AI Chef! Type your ingredients or tap the
    attach icon in the message bar to drop in a fridge photo. Add a cookbook PDF in the sidebar for extra grounding.</div>
    """,
    unsafe_allow_html=True,
)

# --- 2. Pydantic Schema ---
class Recipe(BaseModel):
    title: str = Field(description="Name of the dish")
    cook_time: str = Field(description="Estimated preparation and cooking time (e.g., '25 mins')")
    difficulty: str = Field(description="Skill level required: Easy, Medium, or Hard")
    ingredients_used: list[str] = Field(description="Ingredients detected or provided that are used in this recipe")
    missing_pantry_items: list[str] = Field(description="Common household items needed (e.g., salt, olive oil)")
    instructions: list[str] = Field(description="Sequential step-by-step cooking directions")

# Models that show up in Groq's model list but aren't chat/vision models
# (transcription, TTS, safety-classifier, embedding models) — filtered out
# so the "pick a fallback model" logic never accidentally selects one of these.
_NON_CHAT_MODEL_HINTS = ("whisper", "tts", "guard", "moderation", "embed")

# Groq's vision-capable lineup changes over time and model IDs don't
# reliably contain the word "vision" (current models are qwen/qwen3.6-27b
# and qwen/qwen3.8-27b — the old llama-3.2-*-vision models are retired).
# Matching on "vision" alone silently picks a text-only model, which then
# rejects image input with a confusing 400 "content must be a string" error.
# Maintain an explicit priority list, with a heuristic fallback in case
# Groq adds a new multimodal model before this list is updated.
_KNOWN_VISION_MODEL_PRIORITY = [
    "qwen/qwen3.6-27b",
    "qwen/qwen3.8-27b",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
]
_VISION_MODEL_HINTS = ("vision", "scout", "maverick", "qwen3.6", "qwen3.8", "multimodal")


def pick_vision_model(chat_capable_models: list[str]):
    for candidate in _KNOWN_VISION_MODEL_PRIORITY:
        if candidate in chat_capable_models:
            return candidate
    heuristic_matches = [m for m in chat_capable_models if any(h in m.lower() for h in _VISION_MODEL_HINTS)]
    return heuristic_matches[0] if heuristic_matches else None


def encode_image_to_base64(image: Image.Image, max_dim: int = 1024, quality: int = 85) -> str:
    """Downscale + JPEG-encode an image for the vision API call.
    Keeps the upload small (faster, cheaper) without hurting recipe accuracy."""
    img = image.copy()
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail((max_dim, max_dim))
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG", quality=quality)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def make_display_thumbnail(image: Image.Image, max_dim: int = 800) -> Image.Image:
    """Shrink the copy we keep in session history so a long chat session
    (many fridge photos) doesn't quietly balloon memory usage."""
    thumb = image.copy()
    if thumb.mode in ("RGBA", "P"):
        thumb = thumb.convert("RGB")
    thumb.thumbnail((max_dim, max_dim))
    return thumb


def strip_json_fences(raw: str) -> str:
    """Some models wrap JSON in ```json ... ``` despite instructions not to."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
    return text


def call_groq_chat(client: Groq, model: str, content_payload: list, use_json_mode: bool):
    kwargs = dict(
        model=model,
        messages=[{"role": "user", "content": content_payload}],
        temperature=0.3,
    )
    if use_json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    return client.chat.completions.create(**kwargs)


def render_recipe_tabs(recipes_data):
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


def chat_input_supports_attach() -> bool:
    """accept_file on st.chat_input needs Streamlit >= 1.40. Without this
    check, older Streamlit installs would crash immediately on startup."""
    try:
        major, minor = (int(p) for p in st.__version__.split(".")[:2])
        return (major, minor) >= (1, 40)
    except Exception:
        return False


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
            # Cached by file content: re-uploading the same PDF, or any
            # unrelated widget interaction causing a rerun, won't re-parse it.
            @st.cache_data(show_spinner=False)
            def extract_pdf_text(file_bytes: bytes):
                reader = PdfReader(io.BytesIO(file_bytes))
                text = ""
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
                return text, len(reader.pages)

            pdf_text_context, num_pages = extract_pdf_text(uploaded_pdf.getvalue())
            st.success(f"Loaded {num_pages} PDF pages!")
        except Exception as e:
            st.error(f"Error reading PDF: {e}")

# --- 4. Session State Chat History ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello! What ingredients do you have today? Type them out, or tap the + icon in the message bar to attach a fridge photo!"
        }
    ]


@st.cache_data(ttl=3600, show_spinner=False)
def get_available_models(client_api_key: str):
    # NOTE: no leading underscore on client_api_key — that's intentional.
    # A leading underscore tells Streamlit to exclude the arg from the cache
    # key, which previously caused every API key to reuse the *first* key's
    # cached model list. Keeping it a normal (hashed) argument fixes that.
    client = Groq(api_key=client_api_key)
    return [m.id for m in client.models.list().data]


# Display past messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if "image" in msg and msg["image"]:
            st.image(msg["image"], width=260)
        st.markdown(msg["content"])
        if "recipes" in msg:
            render_recipe_tabs(msg["recipes"])

# --- 5. Unified Chat Input ---
SUPPORTS_ATTACH = chat_input_supports_attach()

user_input = ""
attached_files = []
has_submission = False

if SUPPORTS_ATTACH:
    prompt = st.chat_input(
        "Ask for a recipe or type your ingredients...",
        accept_file=True,
        file_type=["jpg", "jpeg", "png"],
    )
    if prompt:
        user_input = prompt.text or ""
        attached_files = prompt["files"] or []
        has_submission = True
else:
    # Fallback for Streamlit < 1.40: separate uploader, reset via a
    # rotating widget key so a sent photo doesn't linger into later turns.
    st.caption("⚠️ Your Streamlit version doesn't support in-bar attachments — using a fallback uploader below.")
    if "photo_uploader_key" not in st.session_state:
        st.session_state.photo_uploader_key = 0
    uploaded_photo = st.file_uploader(
        "📷 Optional: attach a fridge photo before sending",
        type=["jpg", "jpeg", "png"],
        key=f"chat_photo_{st.session_state.photo_uploader_key}",
    )
    typed = st.chat_input("Ask for a recipe or type your ingredients...")
    if typed or uploaded_photo:
        user_input = typed or ""
        attached_files = [uploaded_photo] if uploaded_photo else []
        has_submission = True

if has_submission:
    if not user_input and not attached_files:
        st.stop()

    if not api_key:
        st.error("Please add your Groq API key in secrets or sidebar.")
    else:
        img_obj = None
        if attached_files:
            try:
                img_obj = Image.open(attached_files[0])
            except Exception as e:
                st.error(f"Couldn't read the attached image, try a different file: {e}")

        display_img = make_display_thumbnail(img_obj) if img_obj else None

        user_msg = {
            "role": "user",
            "content": user_input if user_input else "What can I cook with these ingredients?",
            "image": display_img,
        }
        st.session_state.messages.append(user_msg)

        with st.chat_message("user"):
            if display_img:
                st.image(display_img, width=260)
            if user_input:
                st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Chef AI is cooking up recipes..."):
                try:
                    client = Groq(api_key=api_key)

                    available_models = get_available_models(api_key)
                    chat_capable = [
                        m for m in available_models
                        if not any(hint in m.lower() for hint in _NON_CHAT_MODEL_HINTS)
                    ] or available_models  # last resort: use the raw list if filtering wiped it out

                    if not chat_capable:
                        raise RuntimeError("No chat-capable Groq models are available for this API key.")

                    if img_obj:
                        selected_model = pick_vision_model(chat_capable)
                        if not selected_model:
                            raise RuntimeError(
                                "No vision-capable model is currently available on this Groq "
                                "account to analyze images. Try again with text only, or check "
                                "console.groq.com/docs/vision for the current model names."
                            )
                    else:
                        selected_model = "llama-3.3-70b-versatile" if "llama-3.3-70b-versatile" in chat_capable else chat_capable[0]

                    prompt_text = (
                        f"You are an expert chef. Analyze the user request, image (if provided), and cookbook context.\n"
                        f"Generate 3 distinct recipes.\n\n"
                        f"User Message: {user_input if user_input else 'What can I cook with these ingredients?'}\n"
                        f"Dietary Restrictions: {', '.join(dietary_pref) if dietary_pref else 'None'}\n"
                        f"Skill Level: {skill_level}\n"
                        f"Cookbook Text Context: {pdf_text_context[:4000] if pdf_text_context else 'None'}\n\n"
                        f"Return ONLY valid JSON matching this structure, with no markdown code fences:\n"
                        f"{{\n"
                        f'  "recipes": [\n'
                        f'    {{\n'
                        f'      "title": "Recipe Name",\n'
                        f'      "cook_time": "20 mins",\n'
                        f'      "difficulty": "Easy",\n'
                        f'      "ingredients_used": ["Item 1", "Item 2"],\n'
                        f'      "missing_pantry_items": ["Salt"],\n'
                        f'      "instructions": ["Step 1...", "Step 2..."]\n'
                        f'    }}\n'
                        f'  ]\n'
                        f"}}\n"
                    )

                    content_payload = []
                    if img_obj:
                        base64_image = encode_image_to_base64(img_obj)
                        content_payload.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        })
                    content_payload.append({"type": "text", "text": prompt_text})

                    # Try structured JSON mode first; some models/combinations
                    # (e.g. certain vision models) reject response_format, so
                    # fall back to plain generation + manual parsing if needed.
                    try:
                        response = call_groq_chat(client, selected_model, content_payload, use_json_mode=True)
                    except Exception:
                        response = call_groq_chat(client, selected_model, content_payload, use_json_mode=False)

                    raw_json = strip_json_fences(response.choices[0].message.content)
                    parsed_data = json.loads(raw_json)
                    recipes_data = parsed_data.get("recipes", [parsed_data])

                    assistant_text = "Here are 3 custom recipes I created for you based on your request:"
                    st.markdown(assistant_text)
                    render_recipe_tabs(recipes_data)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_text,
                        "recipes": recipes_data
                    })

                    if not SUPPORTS_ATTACH and attached_files:
                        st.session_state.photo_uploader_key += 1
                        st.rerun()

                except json.JSONDecodeError:
                    st.error("The chef's response wasn't valid JSON — please try again, maybe with a simpler request.")
                except Exception as e:
                    st.error(f"Error generating recipes: {e}")
