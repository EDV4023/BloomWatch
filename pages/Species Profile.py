import streamlit as st
import requests
from bs4 import BeautifulSoup
from streamlit_carousel import carousel

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

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"}
species_name = st.query_params.species
species_type = st.query_params.type

# Try scraping All About Birds first
allaboutbirds_url = f"https://www.allaboutbirds.org/guide/{species_name.replace(' ', '_').title()}/"
image_list = []
overview = ""
scientific_name = ""
audio_link = ""

try:
    response = requests.get(allaboutbirds_url, headers=headers, timeout=5)
    if response.status_code == 200:
        bird_soup = BeautifulSoup(response.text, "html.parser")
        
        # 1. Hero Image
        hero_section = bird_soup.find("section", class_="hero-wrap")
        if hero_section and "url(" in hero_section.get("style", ""):
            img_url = hero_section.get("style").split('url("')[1].split('"')[0]
            image_list.append(dict(title="Species", text=species_name, img=img_url))

        # 2. Scientific Name
        sci_elem = bird_soup.select(".species-info em")
        if sci_elem:
            scientific_name = sci_elem[0].text

        # 3. Range Map
        narrow_content = bird_soup.find("div", class_="narrow-content")
        if narrow_content:
            map_img = narrow_content.find("img")
            if map_img:
                interchange = map_img.get("data-interchange", "")
                map_src = ""
                if interchange:
                    parts = [p.strip() for p in interchange.split(",") if "http" in p]
                    if parts:
                        map_src = parts[-1].replace("[", "").replace("]", "").split(" ")[0]
                if not map_src:
                    map_src = map_img.get("src", "")
                if map_src:
                    image_list.append(dict(title="Range Map", text=f"{species_name} Range", img=map_src))

        # 4. Audio
        audio_tag = bird_soup.find("audio", id="jp_audio_0")
        if audio_tag and audio_tag.has_attr("src"):
            audio_link = audio_tag["src"]
        else:
            audio_player = bird_soup.find("div", class_="player-audio")
            if audio_player and audio_player.has_attr("name"):
                audio_link = audio_player["name"]

        # 5. Overview Description
        overview_heading = bird_soup.find("h2", class_="overview")
        if overview_heading:
            for sibling in overview_heading.find_next_siblings():
                if sibling.name == "p" and sibling.text.strip():
                    overview = sibling.text.strip()
                    break
except Exception:
    pass  # Fall back gracefully if blocked or connection times out

# Fallback / Complement with Wikipedia & Xeno-Canto if scraping was blocked or incomplete
wiki_search_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{species_name.replace(' ', '_')}"
wiki_res = requests.get(wiki_search_url, headers={"User-Agent": "BloomWatch/1.0"})
wiki_page_url = f"https://en.wikipedia.org/wiki/{species_name.replace(' ', '_')}"

if wiki_res.status_code == 200:
    wiki_data = wiki_res.json()
    if not overview and "extract" in wiki_data:
        overview = wiki_data["extract"]
    if not image_list and "thumbnail" in wiki_data:
        image_list.append(dict(title="Specimen Photo", text=species_name, img=wiki_data["thumbnail"]["source"].replace("s.jpg", "800px.jpg")))
    if "content_urls" in wiki_data and "desktop" in wiki_data["content_urls"]:
        wiki_page_url = wiki_data["content_urls"]["desktop"]["page"]

# Render Header & Badge
title_str = f"{species_name} (*{scientific_name}*)" if scientific_name else species_name
st.title(title_str)
st.badge(label=species_type, color=color_map.get(species_type, "green"))

# Display Carousel
if not image_list:
    image_list.append(dict(title="Specimen Photo", text=species_name, img="https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg"))

carousel(items=image_list, container_height=500)

# Render Audio (Check All About Birds audio link first; if blocked, pull from Xeno-Canto API)
if species_type == "Bird" or "Bird" in str(species_type) or species_type == "Animal":
    st.subheader("Bird Audio Call / Chirp")
    if audio_link:
        st.audio(audio_link)
    else:
        try:
            xc_res = requests.get(f"https://www.xeno-canto.org/api/2/recordings?query={species_name.replace(' ', '_')}")
            xc_data = xc_res.json()
            if xc_data.get("recordings") and len(xc_data["recordings"]) > 0:
                rec = xc_data["recordings"][0]
                st.audio("https:" + rec["file"])
                st.caption(f"Audio recorded by {rec.get('rec', 'Unknown')} in {rec.get('loc', 'Unknown')} (Xeno-Canto)")
            else:
                st.info("No audio recordings found for this species.")
        except Exception:
            st.info("Audio lookup currently unavailable.")

# Display Description
if overview:
    st.write(overview.replace('"', ""))

# Extra Info Links
st.subheader("Extra Info")
col_a, col_b = st.columns(2)
with col_a:
    st.page_link(label="All About Birds Guide", page=allaboutbirds_url, icon=":material/info:")
with col_b:
    st.page_link(label="Wikipedia Entry", page=wiki_page_url, icon=":material/menu_book:")