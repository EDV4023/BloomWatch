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

# Global Dark Theme Styling & Card Containers
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
    
    /* Primary Accent Buttons */
    .stButton button {
        background-color: #10b981;
        color: #ffffff;
        border: none;
        border-radius: 0.5rem;
        width: 100%;
        font-weight: 600;
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
# - Hidden pages are registered so st.switch_page() / st.page_link() recognize them safely.
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
    # Render Dual-Card Account Management Screen on Homepage
    st.title("Account Management")
    st.markdown("<p style='color: #9ca3af; margin-bottom: 2rem;'>Sign in or create an account to securely save and sync your personal field notes.</p>", unsafe_allow_html=True)

    # Side-by-side columns matching the dark UI reference image
    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.subheader("Sign In")
            with st.form("Login_Card_Form"):
                login_username = st.text_input("Username", placeholder="Enter username", max_chars=12)
                login_password = st.text_input("Password", type="password", placeholder="••••••••", max_chars=12)
                
                submitted_login = st.form_submit_button("Sign In")
                if submitted_login and users_dict and (login_username in users_dict.keys()) and (len(login_username) >= 6) and (len(login_password) >= 6):
                    if (users_dict[login_username]['password'] == login_password):
                        st.session_state['loggedin'] = True
                        st.session_state.username = login_username
                        st.session_state.password = login_password
                        st.session_state.points = int(users_dict[login_username]["points"])
                        st.session_state.plants = list(users_dict[login_username]["plants"])
                        st.session_state.animals = list(users_dict[login_username]["animals"])
                        st.session_state.flowers = list(users_dict[login_username]["flowers"])
                        st.session_state.pollinator = list(users_dict[login_username]["pollinators"])
                        st.session_state.non_native = list(users_dict[login_username]["non_native"])
                        st.session_state.history = []

                        st.switch_page("pages/Camera.py")

    with col2:
        with st.container(border=True):
            st.subheader("Create Account")
            # If you have a separate signup page logic, you can point them to switch_page or embed the signup form here.
            st.markdown("<p style='color: #9ca3af; font-size: 0.9rem;'>New field naturalist? Register your profile to start logging observations.</p>", unsafe_allow_html=True)
            
            if st.button("Go to Registration"):
                st.switch_page("pages/Sign Up.py")