import streamlit as st
from firebase_admin import db

if "loggedin" not in st.session_state:
    st.switch_page("Homepage.py")

st.title("Points Leaderboard")

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
        st.write(f"{i}. {l[i-1][0]} - {l[i-1][1]}") 
except:
    st.write()