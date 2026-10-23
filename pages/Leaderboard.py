import streamlit as st
from firebase_admin import db

if "loggedin" not in st.session_state:
    st.switch_page("Homepage.py")

st.title("Points Leaderboard")

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

ref = db.reference("users").get()
l = []

for i in ref:
    l.append((i, ref[i]["points"]))

def s(tup):
    return tup[1] 

l.sort(key = s, reverse = True) 
leaderboard = l[0:11]

# Write as many people on leaderboard as possible
try:
    for i in range(1,11):
        st.write(f"**{i}.** {l[i-1][0]}: {l[i-1][1]}") 
except:
    st.write()