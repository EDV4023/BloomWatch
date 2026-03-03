import geocoder
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from google import genai
from google.genai import types
import numpy as np
import cv2
import streamlit as st
import firebase_admin
from firebase_admin import credentials, db

st.title("BloomWatch")

# if "loggedin" not in st.session_state:
#     st.session_state.loggedin = False

# Ensure that firebase database does not continously reinitialize, so we store it in a cache
@st.cache_resource
def initialize_firebase():
    cred = credentials.Certificate(dict(st.secrets.firebase_credentials))
    return firebase_admin.initialize_app(cred, {"databaseURL" : st.secrets["database_url"]})

if "init_run" not in st.session_state:
    app = initialize_firebase()

st.session_state.init_run = False

users_ref = db.reference('users')
users_dict = users_ref.get()

with st.form("Login"):
    st.header('Log In')
    username = st.text_input("**Username**", help = "Name you are seen with online", placeholder = "Enter username", max_chars = 12)
    password = st.text_input("**Password**", help = "Enter a strong password", type = "password", placeholder = "Enter password", max_chars = 12)
    login = st.form_submit_button("Log In")
    if login and (username in users_dict.keys()) and (len(username) >= 6) and (len(password) >= 6):
        if (users_dict[username]['password'] == password):
            st.success("Succesfully logged in")

            # Initialize user data in session state:
            st.session_state['loggedin'] = True
            st.session_state.username = username
            st.session_state.password = password
            st.session_state.points = int(users_dict[username]["points"])
            st.session_state.plants = list(users_dict[username]["plants"])
            st.session_state.animals = list(users_dict[username]["animals"])
            st.session_state.flowers = list(users_dict[username]["flowers"])
            st.session_state.pollinator = list(users_dict[username]["pollinators"])
            st.session_state.non_native = list(users_dict[username]["non_native"])
            st.session_state.history = []



            
st.page_link(page = r"pages/Sign Up.py", label = "Sign Up")
if "loggedin" in st.session_state:
    if st.session_state.loggedin:
        st.page_link(page = r"pages/Camera.py", label = "Next")

# Testing firebase database
# db.reference("users").set({})
# db.reference("users").push({"name": "bob", "password": 123})
