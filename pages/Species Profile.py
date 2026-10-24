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

st.html("""
<style>
    .stApp {
        background-color: #0b0f19;
        color: #f3f4f6;
    }
    [data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #1f2937;
    }
    div.stMarkdown, div.stButton {
        color: #f3f4f6;
    }
    .stButton button {
        background-color: #10b981;
        color: #ffffff;
        border: none;
        border-radius: 0.5rem;
    }
    .stButton button:hover {
        background-color: #059669;
        color: #ffffff;
    }
</style>
""")

species_name = st.query_params.species
species_type = st.query_params.type

# Fetch Data from Wikipedia API
headers = {"User-Agent": "BloomWatch/1.0 (Conservation App)"}
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

# Render image with normal width
if image_url:
    st.image(image_url, caption=species_name, width=400)
else:
    st.image("https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg", caption="No image available", width=300)

# Render Audio Call / Chirp if Bird or Animal
if species_type == "Bird" or "Bird" in str(species_type) or species_type == "Animal":
    st.subheader("Bird Audio Call / Chirp")
    audio_found = False
    try:
        # Use '+' or spaces for Xeno-Canto query instead of underscores
        query_str = species_name.replace(' ', '+')
        xc_res = requests.get(f"https://www.xeno-canto.org/api/2/recordings?query={query_str}")
        if xc_res.status_code == 200:
            xc_data = xc_res.json()
            if xc_data.get("recordings") and len(xc_data["recordings"]) > 0:
                rec = xc_data["recordings"][0]
                audio_file = rec.get("file", "")
                if audio_file:
                    if audio_file.startswith("//"):
                        audio_file = "https:" + audio_file
                    st.audio(audio_file)
                    st.caption(f"Audio recorded by {rec.get('rec', 'Unknown')} in {rec.get('loc', 'Unknown')} via Xeno-Canto")
                    audio_found = True
        
        if not audio_found:
            st.info(f"No audio recordings found for '{species_name}' on Xeno-Canto.")
    except Exception as e:
        st.error(f"Audio lookup error: {e}")

# Display Description
st.write(overview)

# Extra Info Links
st.subheader("Extra Info")
st.page_link(label="Wikipedia Entry", page=wiki_page_url, icon=":material/menu_book:")