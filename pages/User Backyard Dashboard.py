import streamlit as st
import geocoder
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from firebase_admin import db
from google import genai
from google.genai import types

client = genai.Client(api_key = st.secrets.API_KEY)

st.set_page_config(page_title="BloomWatch - Backyard Dashboard", layout="wide")

# Prevent user from bypassing authentication
if "loggedin" not in st.session_state:
    st.switch_page(r"Homepage.py")
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

    
# Load User Data
user_ref = db.reference("users").child(st.session_state.username)
user_data = user_ref.get()
if not user_data:
    st.error("User data not found.")
    st.stop()

# Clean up the lists by removing "PLACEHOLDER" entries
def clean_list(lst):
    if not lst:
        return []
    return [item for item in lst if item != "PLACEHOLDER"]

plants = clean_list(user_data.get("plants", []))
new_plants = [(p, ":green-badge[Plant]") for p in plants]

animals = clean_list(user_data.get("animals", []))
new_animals = [(a, ":blue-badge[Animal]") for a in animals]

flowers = clean_list(user_data.get("flowers", []))
new_flowers = [(f, ":violet-badge[Flowering Plant]") for f in flowers]

pollinators = clean_list(user_data.get("pollinators", []))
new_pollinators = [(pl, ":yellow-badge[Pollinator]") for pl in pollinators]

non_native = clean_list(user_data.get("non_native", []))
new_nn = [(n, ":red-badge[Non-Native/Invasive Species]") for n in non_native]

total_points = user_data.get("points", 0)

combined_species_list = new_plants + new_animals + new_flowers + new_pollinators + new_nn

def user_location() -> tuple[str, str] | None:
    users_ref = db.reference(f"users/{st.session_state.username}")
    users_dict = users_ref.get()
    if users_dict:
        return users_dict.get("city"), users_dict.get("state")
    else:
        return None

if "history" not in st.session_state:
    st.session_state.history = []

if "show_ai_advisor" not in st.session_state:
    st.session_state.show_ai_advisor = False

st.title("Backyard Sightings Log & AI Advisor")
st.markdown("<p style='color: #9ca3af; margin-bottom: 1.5rem;'>Review logged specimens, track ecosystem scores, and get Gemini recommendations to improve your backyard biodiversity.</p>", unsafe_allow_html=True)

# Dashboard Header Card (Location & Points Metrics)
with st.container(border=True):
    city, state = user_location()
    if city and state:
        st.markdown(f"**Location:** {city}, {state}")
    st.metric(label="Total Points", value=user_data.get("points", 0))

st.divider()

# Display Sightings History inside a Structured Container Card
with st.container(border=True):
    st.subheader("Logged Sightings Table")
    if combined_species_list:
        for entry in combined_species_list:
            species_info, species_profile = st.columns(2)
            with species_info:
                st.write(f"{entry[0]}: {entry[1]}")
            with species_profile:
                st.page_link(page = r"pages/Species Profile.py", label = "Species Profile", query_params = {"species" : entry[0], "type" : entry[1].split("[")[1][:-1]})

        species_count = {}
        for entry in combined_species_list:
            species_count[entry[0]] = species_count.get(entry[0], 0) + 1
        
        st.divider()
        st.subheader("Species Breakdown")
        st.bar_chart(species_count)

        st.divider()
        st.subheader("Unique Species")

        pl, an, fl, po, no = st.tabs(["Plants", "Animals", "Flowering Plants", "Pollinators", "Non-Native"])

        with pl:
            for i in set(plants):
                st.write("*"+i+"*")
        with an:
            for i in set(animals):
                st.write("*"+i+"*")
        with fl:
            for i in set(flowers):
                st.write("*"+i+"*")
        with po:
            for i in set(pollinators):
                st.write("*"+i+"*")
        with no:
            for i in set(non_native):
                st.write("*"+i+"*")
    else:
        st.info("No logged sightings yet. Use the Field Scanner to identify specimens.")

st.divider()

color_map = {
    "Plant" : "green",
    "Animal" : "blue",
    "Flowering Plant": "violet",
    "Pollinator": "yellow",
    "Non-Native/Invasive Species": "red"
}

# AI Improvement Guide Section inside Dark-Green Styled Card Container
with st.container(border=True):
    st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(6, 78, 59, 0.4) 0%, rgba(2, 44, 34, 0.7) 100%); border: 1px solid #10b981; border-radius: 0.75rem; padding: 1.5rem; box-shadow: 0 0 15px rgba(16, 185, 129, 0.2);">
            <h3 style="color: #10b981; margin-top: 0; display: flex; align-items: center; gap: 0.5rem;">
                🤖 Gemini Backyard Biodiversity Advisor
            </h3>
            <p style="color: #9ca3af; margin-bottom: 1.2rem;">
                Generate a custom enhancement plan for your backyard based on your region and logged species.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    
    if not st.session_state.show_ai_advisor:
        if st.button("🤖 Generate Improvement Plan", type="primary"):
            st.session_state.show_ai_advisor = True
            st.rerun()
    else:
        if st.button("Hide Improvement Plan"):
            st.session_state.show_ai_advisor = False
            st.rerun()
            
        st.write("")
        for i in set(non_native):
            st.write("- Remove: *:red["+i+"]*")
            
        with st.spinner("Analyzing ecosystem and compiling recommendations..."):
            try:
                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents = f"Recommend 10 more native (In Location {city}, {state}) plants, animals, and flowering plants to increase the user's biodiversity, and make it more pollinator friendly for the user's backyard. Recommend species that can be found in the user's backyard at their location, so nothing outlandish. Current user's backyard {combined_species_list}. Only list out specific species with their COMMON NAME (No Scientific Name) in dash format. Do not include any greetings, formalities, any starting text, any other text that isn't the dash format stated, or text like \"Here are some recommendations\", just list new species in format: - SPECIES_NAME||Plant, Animal, Flowering Plant or Pollinator \nSPECIES_NAME||Plant, Animal, Flowering Plant or Pollinator \nSPECIES_NAME||Plant, Animal, Flowering Plant or Pollinator"
                )

                st.write("**Possible New Additions to Look Out for:**")
                for i in response.text.split("\n"):
                    if "||" in i:
                        species = i.split("||")[0].replace("-","").strip()
                        species_type = i.split("||")[1].strip()

                        recc_info, recc_profile = st.columns(2)
                        with recc_info:
                            st.write(f"- {species}: :{color_map.get(species_type, 'green')}-badge[{species_type}]")
                        with recc_profile:
                            st.page_link(page = r"pages/Species Profile.py", label = "Species Profile", query_params = {"species" : species, "type" : species_type})

            except Exception as e:
                st.error(f"Could not generate recommendations at this time: {e}")