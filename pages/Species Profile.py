import streamlit as st
import requests
from bs4 import BeautifulSoup

if "species" not in st.query_params:
    # Prevent user from bypassing authentication
    if "loggedin" not in st.session_state:
        st.switch_page(r"Homepage.py")
    st.switch_page(r"pages/User Backyard Dashboard.py")

headers={"User-Agent": "BloomWatch/1.0"}

search_url = f"https://en.wikipedia.org/w/index.php?search={st.query_params.species}&title=Special%3ASearch&profile=advanced&fulltext=1&ns0=1"
search_response = requests.get(search_url, headers = headers)
soup = BeautifulSoup(search_response, "html.parser")

list_tags = soup.find_all("li", attrs = {"class":"mw-search-result mw-search-result-ns-0"})
for list_item in list_tags:
    if "placeholder" not in list_item.text:
        result_tag = list_item

soup = BeautifulSoup(result_tag, "html.parser")
title = soup.find("a").get("title")

url = fr"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(" ", "_")}"
response = requests.get(url, headers = headers).json()


st.title(f"**{st.query_params.species}**")

if "thumbnail" in response:
    st.image(response["thumbnail"]["source"])