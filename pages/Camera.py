import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import io
import json
from firebase_admin import db

st.set_page_config(
    page_title="BloomWatch - AI Field Scanner",
    layout="wide"
)

# Prevent user from bypassing authentication
if "loggedin" not in st.session_state:
    st.switch_page("Homepage.py")

# Global Dark Theme Styling
st.html("""
<style>
    /* Global App Background & Text */
    .stApp {
        background-color: #0b0f19;
        color: #f3f4f6;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #1f2937;
    }
    
    /* Card & Container Polish */
    div.stMarkdown, div.stButton {
        color: #f3f4f6;
    }
    
    /* Primary Accent Buttons */
    .stButton button {
        background-color: #10b981;
        color: #ffffff;
        border: none;
        border-radius: 0.5rem;
        font-weight: 600;
    }
    .stButton button:hover {
        background-color: #059669;
        color: #ffffff;
    }
</style>
""")

st.title("AI Field Scanner")
st.markdown("<p style='color: #9ca3af; margin-bottom: 1.5rem;'>Capture or upload a picture for instant taxonomic identification.</p>", unsafe_allow_html=True)

# Initialize Gemini client using app secrets
try:
    client = genai.Client(api_key=st.secrets.API_KEY)
except Exception as e:
    st.error("Gemini API key not found in secrets. Please configure st.secrets.API_KEY.")
    st.stop()

# Input Method Selection tabs/radio
input_method = st.radio("Choose Input Method", ["Upload Image", "Capture from Camera"], horizontal=True)

uploaded_image = None

with st.container(border=True):
    if input_method == "Upload Image":
        uploaded_file = st.file_uploader("Upload a plant, flower, or animal image", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            uploaded_image = Image.open(uploaded_file)
    else:
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
                    "Analyze this image. Identify the plant, flower, or bird accurately. "
                    "Return a strict JSON object with exact keys: "
                    "name (common name), latinName, family, description, isBird (boolean), "
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
        st.markdown(f"*{item.get('latinName')}* &bull; **Family:** {item.get('family')}")
        st.markdown(f"<p style='color: #9ca3af; margin-top: 0.5rem;'>{item.get('description')}</p>", unsafe_allow_html=True)

        if st.button("Save to Account Log"):
            try:
                username = st.session_state.get("username")
                if username:
                    user_ref = db.reference(f"users/{username}")
                    user_data = user_ref.get()
                    
                    # Determine category bucket based on taxonomy type
                    category = "animals" if item.get("isBird") else "plants"
                    current_list = user_data.get(category, [])
                    
                    if "PLACEHOLDER" in current_list:
                        current_list = [item.get('name')]
                    elif item.get('name') not in current_list:
                        current_list.append(item.get('name'))
                    
                    new_points = int(user_data.get("points", 0)) + 1

                    user_ref.update({
                        category: current_list,
                        "points": new_points
                    })
                    st.session_state.points = new_points
                    st.success("Specimen successfully saved to your account log and synchronized with Firebase!")
            except Exception as e:
                st.error(f"Failed to save to database: {e}")