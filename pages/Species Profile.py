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
    # Prevent user from bypassing authentication
    if "loggedin" not in st.session_state:
        st.switch_page(r"Homepage.py")
    st.switch_page(r"pages/User Backyard Dashboard.py")

if st.query_params.type not in color_map:
    # Prevent user from bypassing authentication
    if "loggedin" not in st.session_state:
        st.switch_page(r"Homepage.py")
    st.switch_page(r"pages/User Backyard Dashboard.py")


headers={"User-Agent": "BloomWatch/1.0"}

allaboutbirds_search_response = requests.get(f"https://www.allaboutbirds.org/guide/{st.query_params.species.replace(" ", "_").title()}/", headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"})
bird_soup = BeautifulSoup(allaboutbirds_search_response.text, "html.parser")

find_hero_wrap = bird_soup.find_all("section", attrs = {"class" : "hero-wrap"})

if not find_hero_wrap:
    if "Invasive" in st.query_params.type:
        search_url = f"https://en.wikipedia.org/w/index.php?search={st.query_params.species}&title=Special%3ASearch&profile=advanced&fulltext=1&ns0=1"
    else:
        search_url = f"https://en.wikipedia.org/w/index.php?search={st.query_params.species} ({st.query_params.type})&title=Special%3ASearch&profile=advanced&fulltext=1&ns0=1"

    search_response = requests.get(search_url, headers = headers)
    soup = BeautifulSoup(search_response.text, "html.parser")

    list_tags = soup.find_all("li", attrs = {"class":"mw-search-result mw-search-result-ns-0"})
    first_result = list_tags[0]
    result_tag = None
    for list_item in list_tags:
        if "placeholder" not in str(list_item):
            result_tag = list_item
            break

    title = result_tag.find("a").get("title")

    first_title = first_result.find("a").get("title")

    url = fr"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(" ", "_")}"
    response = requests.get(url, headers = headers).json()


    st.title(st.query_params.species)
    st.badge(label = st.query_params.type, color = color_map[st.query_params.type])

    if "thumbnail" in response:
        st.image(response["thumbnail"]["source"])

    url = fr"https://en.wikipedia.org/api/rest_v1/page/summary/{first_title.replace(" ", "_")}"
    response = requests.get(url, headers = headers).json()

    if "extract" in response:
        st.write(response["extract"])

    st.subheader("**Extra Info**")
    st.page_link(label = "Wikipedia", page = f"https://en.wikipedia.org/wiki/{first_title}", icon = ":material/info:")

else:
    image_link = find_hero_wrap[0].get("data-interchange").split(",")[0].replace("[","").replace("]","").split(",")[0]

    scientific_name = bird_soup.select(".species-info em")[0].text

    bird_map_url = f"https://www.allaboutbirds.org/guide/{st.query_params.species.replace(" ", "_")}/maps-range" 
    range_map_response = requests.get(bird_map_url, headers = headers)
    range_map_soup = BeautifulSoup(range_map_response.text, "html.parser")
    st.write(bird_map_url)
    range_map = range_map_soup.find("img", attrs = {"id" : "dlwhls-interchange"})
    st.write(range_map)

    image_list = [
        dict(text = st.query_params.species, img = image_link),
        dict(text = f"{st.query_params.species} Range Map", img = range_map)
    ]

    st.title(f"{st.query_params.species} (*{scientific_name}*)")
    st.badge(label = st.query_params.type, color = color_map[st.query_params.type])

    carousel(items = image_list)

    audio_link = find_hero_wrap[0].find("div", attrs = {"class" : "jp-jplayer player-audio"}).get("name")
    st.audio(audio_link)

    overview = bird_soup.select(".speciesInfoCard.float.clearfix p")[0].text

    st.write(overview.replace("\"", ""))

    st.subheader("**Extra Info**")
    st.page_link(label = "All About Birds", page = f"https://www.allaboutbirds.org/guide/{st.query_params.species.replace(" ", "_").title()}/", icon = ":material/info:")