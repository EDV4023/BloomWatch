import streamlit as st
import pandas as pd
from firebase_admin import db

if "loggedin" not in st.session_state:
    st.switch_page("Homepage.py")

st.title("Points Leaderboard")
st.markdown("<p style='color: #9ca3af; margin-bottom: 1.5rem;'>Top conservation observers ranked by net biodiversity score and contribution points.</p>", unsafe_allow_html=True)

# Add this near the top of every page script right after st.set_page_config()
# 1. Inject the Flexbox reordering CSS and Brand HTML
st.html("""
<style>
    /* Global Sidebar Background & Padding */
    [data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #1f2937;
        padding-top: 1rem;
    }
    
    /* Enlarge sidebar text and navigation links */
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] a, 
    [data-testid="stSidebar"] div {
        font-size: 1.15rem !important;
    }
    
    [data-testid="stSidebar"] a {
        padding: 0.6rem 0.8rem !important;
    }

    /* Force the sidebar layout to flex so we can reorder items */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        display: flex;
        flex-direction: column;
    }
    
    /* Pull our custom brand container to the absolute top (-100) */
    .sidebar-brand-wrapper {
        order: -100 !important;
        margin-bottom: 1.5rem;
    }
</style>
""")

# 2. Render the Brand Header (it will automatically jump to the top due to order: -100)
with st.sidebar:
    st.html("""
        <div class="sidebar-brand-wrapper" style="display: flex; align-items: center; gap: 0.5rem; font-size: 1.5rem; font-weight: 700; color: #10b981; text-shadow: 0 0 12px rgba(16, 185, 129, 0.6); padding-left: 0.5rem;">
            <span style="font-size: 1.6rem; filter: drop-shadow(0 0 8px rgba(16, 185, 129, 0.9));">🌿</span>
            <span style="color: #10b981; text-shadow: 0 0 12px rgba(16, 185, 129, 0.7);">BloomWatch</span>
        </div>
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