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
from pathlib import Path

st.set_page_config(
    page_title="BloomWatch - Flora & Fauna Intelligence",
    page_icon="🌿",
    layout="wide"
)

# Add this near the top of every page script right after st.set_page_config()
# 1. Render the glowing green BloomWatch header ONCE at the top of the sidebar
with st.sidebar:
    st.html("""
        <div style="display: flex; align-items: center; gap: 0.5rem; font-size: 1.5rem; font-weight: 700; color: #10b981; text-shadow: 0 0 12px rgba(16, 185, 129, 0.6); margin-bottom: 1.5rem; padding-left: 0.5rem;">
            <span style="font-size: 1.6rem; filter: drop-shadow(0 0 8px rgba(16, 185, 129, 0.9));">🌿</span>
            <span style="color: #10b981; text-shadow: 0 0 12px rgba(16, 185, 129, 0.7);">BloomWatch</span>
        </div>
    """)

# 2. Global Styling & Sidebar Text Enlargement
st.html("""
<style>
    /* Global App Background & Text */
    .stApp {
        background-color: #0b0f19;
        color: #f3f4f6;
    }
    
    /* Sidebar Styling & Text Enlargement */
    [data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #1f2937;
        padding-top: 1rem;
    }
    
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] a, 
    [data-testid="stSidebar"] div {
        font-size: 1.15rem !important;
    }
    
    [data-testid="stSidebar"] a {
        padding: 0.6rem 0.8rem !important;
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

# Safely register active pages using pathlib to avoid file-not-found errors
pages_dir = Path(__file__).parent / "pages"

nav_pages = [
    st.Page(str(pages_dir / "Camera.py"), title="Identify & Capture", icon=":material/camera:"),
    st.Page(str(pages_dir / "Leaderboard.py"), title="Leaderboard", icon=":material/trophy:"),
    st.Page(str(pages_dir / "User Backyard Dashboard.py"), title="Backyard Dashboard", icon=":material/dashboard:")
]

# Optional hidden page registration if the file exists
species_profile_path = pages_dir / "Species Profile.py"
if species_profile_path.exists():
    nav_pages.append(st.Page(str(species_profile_path), title="Species Profile", visibility="hidden"))

pg = st.navigation(nav_pages)

# If the user is logged in, run the navigation router
if st.session_state.get('loggedin', False):
    pg.run()
else:
    # Render Dual-Card Account Management Screen on Homepage matching the dark-green theme
    st.title("Account Management")
    st.markdown("<p style='color: #9ca3af; margin-bottom: 2rem;'>Sign in or create an account to securely save and sync your personal field notes.</p>", unsafe_allow_html=True)

    # Side-by-side columns matching your target UI layout
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

                        st.switch_page(str(pages_dir / "Camera.py"))

    with col2:
        with st.container(border=True):
            st.subheader("Create Account")
            st.markdown("<p style='color: #9ca3af; font-size: 0.9rem; margin-bottom: 1.5rem;'>New field naturalist? Register your profile to start logging observations.</p>", unsafe_allow_html=True)
            
            with st.form("Signup_Card_Form"):
                signup_username = st.text_input("Display Name / Username", placeholder="Field Naturalist", max_chars=12)
                signup_password = st.text_input("Password", type="password", placeholder="••••••••", max_chars=12)
                
                submitted_signup = st.form_submit_button("Register & Sync DB")
                if submitted_signup and signup_username and len(signup_username) >= 6 and len(signup_password) >= 6:
                    if users_dict and signup_username in users_dict.keys():
                        st.error("Username already exists. Please choose another.")
                    else:
                        # Register user in Firebase database
                        db.reference(f'users/{signup_username}').set({
                            "password": signup_password,
                            "points": 0,
                            "plants": ["PLACEHOLDER"],
                            "animals": ["PLACEHOLDER"],
                            "flowers": ["PLACEHOLDER"],
                            "pollinators": ["PLACEHOLDER"],
                            "non_native": ["PLACEHOLDER"],
                            "city": "The Dalles",
                            "state": "Oregon"
                        })
                        st.session_state['loggedin'] = True
                        st.session_state.username = signup_username
                        st.session_state.password = signup_password
                        st.session_state.points = 0
                        st.session_state.plants = []
                        st.session_state.animals = []
                        st.session_state.flowers = []
                        st.session_state.pollinator = []
                        st.session_state.non_native = []
                        st.session_state.history = []

                        st.success("Account created successfully!")
                        st.switch_page(str(pages_dir / "Camera.py"))