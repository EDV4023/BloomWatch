import streamlit as st
import geocoder
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from firebase_admin import db
from google import genai
from google.genai import types

client = genai.Client(api_key = st.secrets.API_KEY)

st.title("Backyard Dashboard")

# Prevent user from bypassing authentication
if "loggedin" not in st.session_state:
    st.switch_page(r"Homepage.py")

#Load User Data
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
    new_plants.append((p,":green[Plant]"))

animals = clean_list(user_data["animals"])
new_animals = []
for a in animals:
    new_animals.append((a,":blue[Animal]"))

flowers = clean_list(user_data["flowers"])
new_flowers = []
for f in flowers:
    new_flowers.append((f,":violet[Flowering Plant]"))

pollinators = clean_list(user_data["pollinators"])
new_pollinators = []
for pl in pollinators:
    new_pollinators.append((pl,":yellow[Pollinator]"))

non_native = clean_list(user_data["non_native"])
new_nn = []
for n in non_native:
    new_nn.append((n,":red[Non-Native/Invasive Species]"))

total_points = user_data["points"]

combined_species_list = new_plants + new_animals + new_flowers + new_pollinators + new_nn

# Tested: Working
def get_latlng() -> tuple[float, float]:
    g = geocoder.ip("me") # Get user's current IP: Need to ask user for permission to access location data

    # If latitude and longitude attribute exsits then extract location data
    if g.latlng:
        lat, long = g.latlng
        return lat, long
    else:
        return None

# Tested: Working
def convert_latlng_to_city(lat: float, long: float) -> str | None:
    geolocator = Nominatim(user_agent = "backyard_environmental_diversity_checker | edanvaiz@gmail.com")

    try:
        location = geolocator.reverse(f"{lat},{long}")

        # Obtain postal code/zip code
        if location and "address" in location.raw:
            address = location.raw["address"]
            return address["town"], address["state"]
        return None
    except (GeocoderTimedOut, GeocoderServiceError):
        return None

# Tested: Working
def user_location() -> str | None:
    lat, long = get_latlng()
    city,state = convert_latlng_to_city(lat, long)
    if city and state:
        return city,state
    else:
        return None


if "history" not in st.session_state:
    st.session_state.history = []

st.divider()
st.header(f"{st.session_state.username}'s Backyard Dashboard")

#Display user location
city,state=user_location()
if city and state:
    st.subheader(f"Location: {city}, {state}")

#Display total points
st.metric(label="Total Points", value=st.session_state.points)

st.divider()

#Display Sightings History
if combined_species_list:
    st.subheader("Sightings History")
    for entry in combined_species_list:
        species_info, species_profile = st.columns(2)
        with species_info:
            st.write(f"{entry[0]}: {entry[1]}")
        with species_profile:
            st.page_link(page = r"pages/Species Profile.py", label = "Species Profile", query_params = {"species" : entry[0]})

    species_count = {}
    for entry in combined_species_list:
        species_count[entry[0]] = species_count.get(entry[0], 0) + 1
    
    st.divider()
    
    st.subheader("Species Breakdown")
    st.bar_chart(species_count)

else:
    st.info("No sightings yet. Start exploring your backyard!")

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

st.divider()

st.subheader("Improvement Guide")
for i in set(non_native):
    st.write("Remove: *:red["+i+"]*")
try:
    response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents = f"Reccomend more native (In Location {city}, {state}) plants, animals, and flowering plants to increase the user's biodiversity, and make it more pollinator friendly. Current user's backyard {combined_species_list}. Only list out specific species with their common name in dash format. Do not include any greetings, formalities, any starting text, any other text that isn't the dash format stated, or text like \"Here are some reccomendations\", just list new species in format: - Add SPECIES_NAME \n - Add SPECIES_NAME \n - Add SPECIES_NAME")
    st.write("**Possible New Additions to Look Out for:**")
    st.write(response.text)
except:
    st.space()