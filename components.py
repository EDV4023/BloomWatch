import streamlit as st

def apply_global_theme():
    # 1. Native Streamlit Logo (replace with your actual image path or URL)
    st.logo("logo.png", size = "large")

    # 2. Global Dark Theme, Container Fills, and Button Styling CSS
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
        
        /* Universal Grey Fill for ALL Bordered Containers / Cards */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #111827 !important;
            border: 1px solid #1f2937 !important;
            border-radius: 0.75rem !important;
            padding: 0.5rem;
        }

        /* Card & Container Polish */
        div.stMarkdown, div.stButton {
            color: #f3f4f6;
        }
        
        /* Accent Buttons: Black text normally, turns white on hover */
        .stButton button {
            background-color: #10b981 !important;
            color: #000000 !important;
            border: none;
            border-radius: 0.5rem;
            font-weight: 600;
            transition: background-color 0.2s ease, color 0.2s ease;
        }
        .stButton button:hover {
            background-color: #059669 !important;
            color: #ffffff !important;
        }
    </style>
    """)