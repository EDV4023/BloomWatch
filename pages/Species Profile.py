import streamlit as st
import requests
from bs4 import BeautifulSoup

# Prevent user from bypassing authentication
if "loggedin" not in st.session_state:
    st.switch_page(r"Homepage.py")

if "species" not in st.query_params:
    st.switch_page(r"pages/User Backyard Dashboard.py")

url = f"https://www.google.com/search?sa=X&sca_esv=63d44ac5fb776b6b&cs=1&hl=en-US&sxsrf=ANbL-n6SveGL3IfuU_JkMNPx2ZF-Hml68g:1773956538715&udm=2&fbs=ADc_l-aN0CWEZBOHjofHoaMMDiKpaEWjvZ2Py1XXV8d8KvlI3o6iwGk6Iv1tRbZIBNIVs-6UIUc6UR6SuJFZzmDZDaBCXj3NZJ_DMK_QqUo9V0IfjxG0djCU7QE8UjOr-c7mvKigPhpvaXtoXoq0sQm2jQ3nzq77_uwAjFIqozM0PiKt77NrjKZEM9xM-iXmZlOhSxVOhlRJPU9KCXU7f3N6KQp_hUzZCw&q={st.query_params.species}&ved=2ahUKEwju6diK96yTAxUcnGoFHVZ2Dy0QtKgLegQIFBAB&biw=1440&bih=765&dpr=2"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

st.title(f"**{st.query_params.species}**")

image = soup.find("img", attrs = {"class" : "YQ4gaf"})

st.image(image["src"])