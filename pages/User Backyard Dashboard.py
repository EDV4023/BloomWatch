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

plants = clean_list(user_data["plants"])
new_plants = []
for p in plants:
    new_plants.append((p,":green-badge[Plant]"))

animals = clean_list(user_data["animals"])
new_animals = []
for a in animals:
    new_animals.append((a,":blue-badge[Animal]"))

flowers = clean_list(user_data["flowers"])
new_flowers = []
for f in flowers:
    new_flowers.append((f,":violet-badge[Flowering Plant]"))

pollinators = clean_list(user_data["pollinators"])
new_pollinators = []
for pl in pollinators:
    new_pollinators.append((pl,":yellow-badge[Pollinator]"))

non_native = clean_list(user_data["non_native"])
new_nn = []
for n in non_native:
    new_nn.append((n,":red-badge[Non-Native/Invasive Species]"))

total_points = user_data["points"]

combined_species_list = new_plants + new_animals + new_flowers + new_pollinators + new_nn

# Tested: Working
def user_location() -> tuple[str, str] | None:
    users_ref = db.reference(f"users/{st.session_state.username}")
    users_dict = users_ref.get()
    if users_dict:
        return users_dict["city"], users_dict["state"]
    else:
        return None

if "history" not in st.session_state:
    st.session_state.history = []

st.title("Backyard Sightings Log & AI Advisor")
st.markdown("<p style='color: #9ca3af; margin-bottom: 1.5rem;'>Review logged specimens, track ecosystem scores, and get Gemini recommendations to improve your backyard biodiversity.</p>", unsafe_allow_html=True)

# Dashboard Header Card (Location & Points Metrics)
with st.container(border=True):
    city, state = user_location()
    if city and state:
        st.markdown(f"**Location:** {city}, {state}")
    st.metric(label="Total Points", value=user_data["points"])

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

# AI Improvement Guide Section inside Card Container
with st.container(border=True):
    st.subheader("Backyard Biodiversity Advisor")
    st.markdown("<p style='color: #9ca3af;'>Generate a custom enhancement plan for your backyard based on your region and logged species.</p>", unsafe_allow_html=True)
    
    for i in set(non_native):
        st.write("- Remove: *:red["+i+"]*")
    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents = f"Reccomend 10 more native (In Location {city}, {state}) plants, animals, and flowering plants to increase the user's biodiversity, and make it more pollinator friendly for the user's backyard. Reccomend species that can be found in the user's backyard at their location, so nothing outlandish. Current user's backyard {combined_species_list}. Only list out specific species with their COMMON NAME (No Scientific Name) in dash format. Do not include any greetings, formalities, any starting text, any other text that isn't the dash format stated, or text like \"Here are some reccomendations\", just list new species in format: - SPECIES_NAME||Plant, Animal, Flowering Plant or Pollinator \nSPECIES_NAME||Plant, Animal, Flowering Plant or Pollinator \nSPECIES_NAME||Plant, Animal, Flowering Plant or Pollinator"
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

    except Exception:
        pass