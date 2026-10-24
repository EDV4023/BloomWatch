import streamlit as st
import requests
from bs4 import BeautifulSoup
from streamlit_carousel import carousel

color_map = {
    "Plant" : "green",
    "Animal" : "blue",
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

# Request All About Birds page
allaboutbirds_url = f"https://www.allaboutbirds.org/guide/{species_name.replace(' ', '_').title()}/"
allaboutbirds_search_response = requests.get(allaboutbirds_url, headers=headers)
bird_soup = BeautifulSoup(allaboutbirds_search_response.text, "html.parser")

find_hero_wrap = bird_soup.find_all("section", attrs={"class" : "hero-wrap"})

if not find_hero_wrap:
    # Fallback to Wikipedia if All About Birds block fails
    if "Invasive" in species_type:
        search_url = f"https://en.wikipedia.org/w/index.php?search={species_name}&title=Special%3ASearch&profile=advanced&fulltext=1&ns0=1"
    else:
        search_url = f"https://en.wikipedia.org/w/index.php?search={species_name} ({species_type})&title=Special%3ASearch&profile=advanced&fulltext=1&ns0=1"

    search_response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(search_response.text, "html.parser")

    list_tags = soup.find_all("li", attrs={"class":"mw-search-result mw-search-result-ns-0"})
    first_result = list_tags[0]
    result_tag = first_result
    for list_item in list_tags:
        if "placeholder" not in str(list_item):
            result_tag = list_item
            break

    title = result_tag.find("a").get("title")
    first_title = first_result.find("a").get("title")

    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}"
    response = requests.get(url, headers=headers).json()

    st.title(species_name)
    st.badge(label=species_type, color=color_map[species_type])

    if "thumbnail" in response:
        st.image(response["thumbnail"]["source"])

    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{first_title.replace(' ', '_')}"
    response = requests.get(url, headers=headers).json()

    if "extract" in response:
        st.write(response["extract"])

    st.subheader("Extra Info")
    st.page_link(label="Wikipedia", page=f"https://en.wikipedia.org/wiki/{first_title}", icon=":material/info:")

else:
    # Extract Hero Image safely
    hero_section = find_hero_wrap[0]
    style_attr = hero_section.get("style", "")
    image_link = ""
    if "url(" in style_attr:
        image_link = style_attr.split('url("')[1].split('"')[0]

    # Extract Scientific Name safely
    scientific_name_elem = bird_soup.select(".species-info em")
    scientific_name = scientific_name_elem[0].text if scientific_name_elem else ""

    # Extract Range Map safely from narrow-content
    range_map = ""
    narrow_content = bird_soup.find("div", class_="narrow-content")
    if narrow_content:
        map_img = narrow_content.find("img")
        if map_img:
            range_map = map_img.get("src", "")

    # Build Carousel Items (Hero Image + Range Map + Gallery Thumbnails)
    image_list = []
    if image_link:
        image_list.append(dict(title="Species", text=species_name, img=image_link))
    if range_map:
        image_list.append(dict(title="Range Map", text=f"{species_name} Range", img=range_map))

    # Pull additional hero gallery images if available from .hero-menu
    hero_menu_items = bird_soup.select(".hero-menu li a")
    for item in hero_menu_items:
        img_tag = item.find("img")
        label_tag = item.find("span", class_="txt-label")
        if img_tag:
            img_src = img_tag.get("src", "")
            label_text = label_tag.text if label_tag else "Gallery Image"
            if img_src and not any(d['img'] == img_src for d in image_list):
                image_list.append(dict(title=label_text, text=species_name, img=img_src))

    st.title(f"{species_name} (*{scientific_name}*)")
    st.badge(label=species_type, color=color_map[species_type])

    if image_list:
        carousel(items=image_list, container_height=500)

    # Extract Audio link directly from the player element attributes in your HTML
    audio_player = bird_soup.find("div", class_="jp-jplayer player-audio")
    if audio_player and audio_player.has_attr("name"):
        audio_link = audio_player["name"]
        st.subheader("Bird Audio Call")
        st.audio(audio_link)

    # Overview description
    overview_elem = bird_soup.select(".speciesInfoCard p")
    if overview_elem:
        overview = overview_elem[0].text
        st.write(overview.replace('"', ""))

    st.subheader("Extra Info")
    st.page_link(label="All About Birds", page=allaboutbirds_url, icon=":material/info:")