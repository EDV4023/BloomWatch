import streamlit as st
import requests

# Prevent user from bypassing authentication
if "loggedin" not in st.session_state:
    st.switch_page(r"Homepage.py")

if "species" not in st.query_params:
    st.switch_page(r"pages/User Backyard Dashboard.py")

headers={"User-Agent": "BloomWatch/1.0"}
url = fr"https://en.wikipedia.org/api/rest_v1/page/summary/{(st.query_params.species).replace(" ", "_")}"
response = requests.get(url, headers = headers).json()


st.title(f"**{st.query_params.species}**")

if "thumbnail" in response:
    st.image(response["thumbnail"]["source"])