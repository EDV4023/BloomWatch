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

st.set_page_config(page_title="BloomWatch - Home", page_icon=None, layout="wide")

# Inject Dark Minimalistic Theme CSS
st.html("""
<style>
    .stApp { background-color: #0b0f19; color: #f3f4f6; }
    [data-testid="stSidebar"] { background-color: #111827; border-right: 1px solid #1f2937; }
    .card { background-color: #111827; border: 1px solid #1f2937; border-radius: 10px; padding: 1.5rem; margin-bottom: 1rem; }
</style>
""")

st.title("Ecosystem Overview")
st.markdown("<p style='color: #9ca3af;'>Track regional biodiversity, identify flora and fauna via AI, and log field sightings.</p>", unsafe_allow_html=True)

# Metric Dashboard Grid
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.metric("Logged Sightings", "0")
    st.markdown('</div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.metric("AI Vision Engine", "Gemini 2.5")
    st.markdown('</div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.metric("Account Session", "Guest")
    st.markdown('</div>', unsafe_allow_html=True)

# Quick Start Guide Card
st.markdown("""
<div class="card">
    <h3>Quick Start Field Guide</h3>
    <p style="color: #9ca3af; font-size: 0.95rem; margin-top: 0.5rem; margin-bottom: 1rem;">
        Use your camera or upload a picture. The system queries the Gemini API, pulls verified Wikipedia records, and extracts bird sound calls automatically.
    </p>
</div>
""", unsafe_allow_html=True)



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

            if st.button("Open Field Scanner", type="primary"):
                st.switch_page("pages/Camera.py")



            
st.page_link(page = r"pages/Sign Up.py", label = "Sign Up")