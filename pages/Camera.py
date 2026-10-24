import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import io
import json
from firebase_admin import db
from components import apply_global_theme

st.set_page_config(
    page_title="BloomWatch - AI Field Scanner",
    layout="wide"
)

# Prevent user from bypassing authentication
if "loggedin" not in st.session_state:
    st.switch_page("Homepage.py")

apply_global_theme()

st.title(":green[Wildlife] Scan")
st.markdown("<p style='color: #9ca3af; margin-bottom: 1.5rem;'>Capture or upload a picture for instant taxonomic identification and score evaluation.</p>", unsafe_allow_html=True)

# Initialize Gemini client using app secrets
try:
    client = genai.Client(api_key=st.secrets.API_KEY)
except Exception as e:
    st.error("Gemini API key not found in secrets. Please configure st.secrets.API_KEY.")
    st.stop()

uploaded_image = None

# Input Method Selection using clean modern tabs with Material Icons
with st.container(border=True):
    tab_upload, tab_camera = st.tabs([":material/upload: Upload Image", ":material/photo_camera: Capture from Camera"])
    
    with tab_upload:
        uploaded_file = st.file_uploader("Upload a plant, flower, or animal image", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            uploaded_image = Image.open(uploaded_file)
            
    with tab_camera:
        camera_file = st.camera_input("Take a photo of wildlife")
        if camera_file is not None:
            uploaded_image = Image.open(camera_file)

if uploaded_image is not None:
    st.image(uploaded_image, caption="Selected Specimen Preview", width=500)
    
    if st.button("Identify Specimen with AI", type="primary"):
        with st.spinner("Querying Gemini AI & Taxonomic Databases..."):
            try:
                # Convert PIL image to bytes for Gemini API transmission
                img_byte_arr = io.BytesIO()
                image_format = uploaded_image.format if uploaded_image.format else 'JPEG'
                uploaded_image.save(img_byte_arr, format=image_format)
                img_bytes = img_byte_arr.getvalue()

                prompt_text = (
                    "Analyze this image. "
                    "1. Identify the species in the image accurately (Common name, latinName, family, description). "
                    "2. Determine if the species is indigenous to the ecosystem or invasive/non-native. "
                    "If it is an invasive species (e.g., Chinese Tallow, Emerald Ash Borer, Kudzu) introduced from another region that actively harms the local environment, "
                    "it MUST be classified as invasive with a score of -1. "
                    "3. Apply the exact hierarchy for points and category evaluation: "
                    "- Invasive = -1 (category: 'non_native') "
                    "- Neither plant nor animal = 0 (category: 'other') "
                    "- Regular plant/vegetation (non-flowering) = 2 (category: 'plants') "
                    "- Wild animal (non-pollinator) = 5 (category: 'animals') "
                    "- Flowering plant = 10 (category: 'flowers') "
                    "- Pollinator = 20 (category: 'pollinators') "
                    "Return a strict JSON object with exact keys: "
                    "name, latinName, family, description, isBird (boolean), category, points (integer), "
                    "wikipediaQuery (exact title string for Wikipedia article lookup). "
                    "No markdown formatting outside the JSON."
                )

                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=[
                        prompt_text,
                        types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")
                    ]
                )

                clean_json = response.text.replace("```json", "").replace("```", "").strip()
                result = json.loads(clean_json)

                st.session_state['last_identified'] = result

            except Exception as e:
                st.error(f"Analysis failed: {e}")

# Display Identification Results and Backend Save Integration
if 'last_identified' in st.session_state and st.session_state['last_identified']:
    item = st.session_state['last_identified']
    
    with st.container(border=True):
        st.subheader(item.get('name'))
        st.markdown(f"*{item.get('latinName')}* &bull; **Family:** {item.get('family')} &bull; **Earns:** `{item.get('points', 0)} Points`")
        st.markdown(f"<p style='color: #9ca3af; margin-top: 0.5rem;'>{item.get('description')}</p>", unsafe_allow_html=True)

        if st.button("Save to Account Log"):
            try:
                username = st.session_state.get("username")
                if username:
                    user_ref = db.reference(f"users/{username}")
                    user_data = user_ref.get() or {}
                    
                    category = item.get("category", "plants")
                    current_list = user_data.get(category, [])
                    
                    if "PLACEHOLDER" in current_list:
                        current_list = [item.get('name')]
                    elif item.get('name') not in current_list:
                        current_list.append(item.get('name'))
                    
                    earned_points = int(item.get("points", 0))
                    new_points = int(user_data.get("points", 0)) + earned_points

                    user_ref.update({
                        category: current_list,
                        "points": new_points
                    })
                    st.session_state.points = new_points
                    st.success(f"Specimen saved! Added {earned_points} points to your account.")
            except Exception as e:
                st.error(f"Failed to save to database: {e}")