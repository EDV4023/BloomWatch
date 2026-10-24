import streamlit as st
import requests

color_map = {
    "Plant": "green",
    "Animal": "blue",
    "Flowering Plant": "violet",
    "Pollinator": "yellow",
    "Non-Native/Invasive Species": "red"
}

if ("species" not in st.query_params) or ("type" not in st.query_params):
    if "loggedin" not in st.session_state:
        st.switch_page("Homepage.py")
    st.switch_page("pages/User Backyard Dashboard.py")

if st.query_params.type not in color_map:
    if "loggedin" not in st.session_state:
        st.switch_page("Homepage.py")
    st.switch_page("pages/User Backyard Dashboard.py")

# Add this near the top of every page script right after st.set_page_config()

# 1. Render the glowing green BloomWatch header ONCE at the top of the sidebar
with st.sidebar:
    st.html("""
        <div style="display: flex; align-items: center; gap: 0.5rem; font-size: 1.5rem; font-weight: 700; color: #10b981; text-shadow: 0 0 12px rgba(16, 185, 129, 0.6); margin-bottom: 1.5rem; padding-left: 0.5rem;">
            <span style="font-size: 1.6rem; filter: drop-shadow(0 0 8px rgba(16, 185, 129, 0.9));">🌿</span>
            <span style="color: #10b981; text-shadow: 0 0 12px rgba(16, 185, 129, 0.7);">BloomWatch</span>
        </div>
    """)


# 2. Global Styling & Sidebar Text Enlargement
st.html("""
<style>
    /* Global App Background & Text */
    .stApp {
        background-color: #0b0f19;
        color: #f3f4f6;
    }
    
    /* Sidebar Styling & Text Enlargement */
    [data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #1f2937;
        padding-top: 1rem;
    }
    
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] a, 
    [data-testid="stSidebar"] div {
        font-size: 1.15rem !important;
    }
    
    [data-testid="stSidebar"] a {
        padding: 0.6rem 0.8rem !important;
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

species_name = st.query_params.species
species_type = st.query_params.type
headers = {"User-Agent": "BloomWatch/1.0 (Conservation App)"}

# 1. Fetch Data from Wikipedia API
wiki_search_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{species_name.replace(' ', '_')}"
wiki_res = requests.get(wiki_search_url, headers=headers)
wiki_page_url = f"https://en.wikipedia.org/wiki/{species_name.replace(' ', '_')}"

image_url = None
overview = "No detailed overview available."

if wiki_res.status_code == 200:
    wiki_data = wiki_res.json()
    if "extract" in wiki_data:
        overview = wiki_data["extract"]
    if "thumbnail" in wiki_data:
        image_url = wiki_data["thumbnail"]["source"].replace("s.jpg", "800px.jpg")
    if "content_urls" in wiki_data and "desktop" in wiki_data["content_urls"]:
        wiki_page_url = wiki_data["content_urls"]["desktop"]["page"]

# Render Header & Badge
st.title(species_name)
st.badge(label=species_type, color=color_map.get(species_type, "green"))

# Render normal, well-sized Streamlit image (no carousel)
if image_url:
    st.image(image_url, caption=species_name, width=400)
else:
    st.image("https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg", caption="No image available", width=300)

# 2. Fetch Bird Call / Audio from Wikimedia Commons API
if species_type == "Bird" or "Bird" in str(species_type) or species_type == "Animal":
    st.subheader("Bird Audio Call / Song")
    audio_url = None
    try:
        commons_api = "https://commons.wikimedia.org/w/api.php"
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": f"{species_name} call OR song OR sound",
            "gsrnamespace": "6",  # Namespace 6 targets Media/Files on Wikimedia Commons
            "gsrlimit": "3",
            "prop": "imageinfo",
            "iiprop": "url",
            "format": "json"
        }
        res = requests.get(commons_api, params=params, headers=headers)
        if res.status_code == 200:
            data = res.json()
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_info in pages.items():
                imageinfo = page_info.get("imageinfo", [])
                if imageinfo:
                    file_url = imageinfo[0].get("url", "")
                    # Accept common audio formats hosted on Commons (.ogg, .oga, .mp3, .wav)
                    if file_url.lower().endswith((".ogg", ".oga", ".mp3", ".wav")):
                        audio_url = file_url
                        break
        
        if audio_url:
            st.audio(audio_url)
            st.caption("Audio sourced from Wikimedia Commons archive")
        else:
            st.info(f"No audio recordings found for '{species_name}'.")
    except Exception as e:
        st.info("Audio lookup currently unavailable.")

# Display Description
st.write(overview)

# Extra Info Links
st.subheader("Extra Info")
st.page_link(label="Wikipedia Entry", page=wiki_page_url, icon=":material/menu_book:")