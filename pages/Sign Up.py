from firebase_admin import db, credentials
import streamlit as st
import firebase_admin
import requests
import pandas
import time

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

# Tested: Working
def user_location_list() -> list[str]:
    csv_path = "uscities.csv"
    final_list = []
    df = pandas.read_csv(csv_path, usecols = ["city", "state_name"])
    for i in df.index:
        final_list.append(f"{df.loc[i, "city"]}, {df.loc[i, "state_name"]}")
    
    return final_list


#Sign-up Form
with st.form("Signup"):
    st.header('Sign Up')
    username = st.text_input("**Username**", help = "Name you are seen with online", placeholder = "Enter username", max_chars = 12)
    password = st.text_input("**Password**", help = "Enter a strong password", type = "password", placeholder = "Enter password", max_chars = 12)
    
    display_list = user_location_list()

    col1, col2 = st.columns(2)
    with col1:
        st.write("**Location:**")
    with col2:
        location = st.selectbox("Location", display_list, index = None, placeholder = "Select your current location...")
    
    signup = st.form_submit_button("Sign Up")
    if signup:
        if (len(username) >= 6) and (len(password) >= 6) and location:
            if (users_dict == None or (username not in users_dict.keys())):
                st.success("Congratulations on making your new account!")
                city, state = location.split(", ")
                st.balloons()
                new_user_ref = db.reference(f'users/{username}')
                new_user_ref.set({'password': password, 'points': 0, 'plants': ["PLACEHOLDER"], "animals" : ["PLACEHOLDER"], "flowers" : ["PLACEHOLDER"], "pollinators" : ["PLACEHOLDER"], "non_native":["PLACEHOLDER"], "city":city, "state":state})
                time.sleep(2)
                st.switch_page(r"Homepage.py")
            else:
                st.error("**Username not availabe**")
        elif signup:
            st.warning("**Password and username must be at least 6 characters in length**")
        