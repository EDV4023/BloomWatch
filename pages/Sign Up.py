from firebase_admin import db, credentials
import streamlit as st
import firebase_admin

# Initialize Firebase
@st.cache_resource
def initialize_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(dict(st.secrets.firebase_credentials))
        return firebase_admin.initialize_app(cred, {"databaseURL" : st.secrets["database_url"]})

if "init_run" not in st.session_state:
    app = initialize_firebase()
st.session_state.init_run = False

#Load Users Safely
users_ref = db.reference('users')
users_dict = users_ref.get()

#Sign-up Form
with st.form("Signup"):
    st.header('Sign Up')
    username = st.text_input("**Username**", help = "Name you are seen with online", placeholder = "Enter username", max_chars = 12)
    password = st.text_input("**Password**", help = "Enter a strong password", type = "password", placeholder = "Enter password", max_chars = 12)
    signup = st.form_submit_button("Sign Up")
    if signup:
        if (len(username) >= 6) and (len(password) >= 6):
            if (users_dict == None or (username not in users_dict.keys())):
                st.success("Congratulations on making your new account!")
                new_user_ref = db.reference(f'users/{username}')
                new_user_ref.set({'password': password, 'points': 0, 'plants': ["PLACEHOLDER"], "animals" : ["PLACEHOLDER"], "flowers" : ["PLACEHOLDER"], "pollinators" : ["PLACEHOLDER"], "non_native":["PLACEHOLDER"]})
                st.page_link(page = r"Homepage.py", label = "Login")
            else:
                st.error("**Username not availabe**")
        elif signup:
            st.warning("**Password and username must be at least 6 characters in length**")
        