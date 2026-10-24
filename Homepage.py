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

st.set_page_config(
    page_title="BloomWatch - Flora & Fauna Intelligence",
    page_icon="🌿",
    layout="wide"
)

# Global Dark Theme Styling
st.html("""
<style>
    /* Global App Background & Text */
    .stApp {
        background-color: #0b0f19;
        color: #f3f4f6;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #1f2937;
    }
    
    /* Card & Container Polish */
    div.stMarkdown, div.stButton {
        color: #f3f4f6;
    }
    
    /* Accent Buttons */
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

# Ensure that firebase database does not continuously reinitialize, so we store it in a cache
@st.cache_resource
def initialize_firebase():
    cred = credentials.Certificate(dict(st.secrets.firebase_credentials))
    return firebase_admin.initialize_app(cred, {"databaseURL" : st.secrets["database_url"]})

if "init_run" not in st.session_state:
    app = initialize_firebase()

st.session_state.init_run = False

users_ref = db.reference('users')
users_dict = users_ref.get()

# Register navigation pages:
# - Visible pages appear in the sidebar navbar with custom icons.
# - Hidden pages are registered so st.switch_page() recognizes them, but they stay out of the navbar.
pg = st.navigation({
    "Main": [
        st.Page("pages/Camera.py", title="Identify & Capture", icon=":material/camera:"),
        st.Page("pages/Leaderboard.py", title="Leaderboard", icon=":material/trophy:"),
        st.Page("pages/User Backyard Dashboard.py", title="Backyard Dashboard", icon=":material/dashboard:")
    ],
    "Hidden": [
        st.Page("pages/Sign Up.py", title="Sign Up", visibility="hidden"),
        st.Page("pages/Species Profile.py", title="Species Profile", visibility="hidden")
    ]
})

# If the user is logged in, run the navigation router
if st.session_state.get('loggedin', False):
    pg.run()
else:
    # Render Login Screen on Homepage when not logged in
    st.title("BloomWatch")

    with st.form("Login"):
        st.header('Log In')
        username = st.text_input("**Username**", help = "Name you are seen with online", placeholder = "Enter username", max_chars = 12)
        password = st.text_input("**Password**", help = "Enter a strong password", type = "password", placeholder = "Enter password", max_chars = 12)
        login = st.form_submit_button("Log In")
        
        if login and users_dict and (username in users_dict.keys()) and (len(username) >= 6) and (len(password) >= 6):
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

                st.switch_page("pages/Camera.py")
                 
    if st.button("Create Account / Sign Up"):
        st.switch_page("pages/Sign Up.py")