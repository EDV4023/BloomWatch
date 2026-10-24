import streamlit as st
import pandas as pd
from firebase_admin import db

if "loggedin" not in st.session_state:
    st.switch_page("Homepage.py")

st.title("Points Leaderboard")
st.markdown("<p style='color: #9ca3af; margin-bottom: 1.5rem;'>Top conservation observers ranked by net biodiversity score and contribution points.</p>", unsafe_allow_html=True)

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

# --- BACKEND LOGIC (Unchanged) ---
ref = db.reference("users").get()
l = []

if ref:
    for i in ref:
        l.append((i, ref[i]["points"]))

    def s(tup):
        return tup[1] 

    l.sort(key = s, reverse = True) 
    leaderboard = l[0:11]
else:
    leaderboard = []

# --- FRONTEND UI RENDERING ---
try:
    if l:
        df_data = []
        for i in range(1, min(11, len(l) + 1)):
            # Assigning gold, silver, and bronze emojis for ranks 1, 2, and 3
            if i == 1:
                rank_display = "🥇 1"
            elif i == 2:
                rank_display = "🥈 2"
            elif i == 3:
                rank_display = "🥉 3"
            else:
                rank_display = str(i)

            df_data.append({
                "Rank": rank_display,
                "Observer": l[i-1][0],
                "Total Points": l[i-1][1]
            })
        
        df = pd.DataFrame(df_data)
        
        # Streamlit native bordered container wrapper
        with st.container(border=True):
            st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.write("No leaderboard data available.")
except Exception:
    st.write("No leaderboard data available.")