import streamlit as st
import requests
from bs4 import BeautifulSoup

if ("species" not in st.query_params) or ("type" not in st.query_params):
    # Prevent user from bypassing authentication
    if "loggedin" not in st.session_state:
        st.switch_page(r"Homepage.py")
    st.switch_page(r"pages/User Backyard Dashboard.py")

headers={"User-Agent": "BloomWatch/1.0"}
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

color_map = {
    "Plant" : "green",
    "Animal" : "blue",
    "Flowering Plant": "violet",
    "Pollinator": "yellow",
    "Non-Native/Invasive Species": "red"
}

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