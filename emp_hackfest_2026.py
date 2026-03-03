import geocoder
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from google import genai
from google.genai import types
import numpy as np
import cv2
import streamlit as st
import firebase_admin
from firebase_admin import credentials, db

client = genai.Client(api_key = st.session_state.API_KEY)

# Ensure that firebase database does not continously reinitialize, so we store it in a cache
@st.cache_resource
def initialize_firebase():
    cred = credentials.Certificate(st.session_state.firebase_credentials)
    return firebase_admin.initialize_app(cred, {"database_url":st.session_state.database_url})

app = initialize_firebase()



# leaderboard = "leaderboard.json"

#Tested: Working
def resize(image):
    max_side = 1200
    height, width = image.shape[0:2]
    scale = max_side / max(height, width)

    if scale < 1:
        image = cv2.resize(image, (int(scale*width),int(scale*height)))
    return image    

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
            return address["town"]
        return None
    except (GeocoderTimedOut, GeocoderServiceError):
        return None

# Tested: Working
def user_location() -> str | None:
    lat, long = get_latlng()
    city = convert_latlng_to_city(lat, long)
    if city:
        return city
    else:
        return None

# Recognized image to be plant, animal, or neither and assigns points (5 for animals, 1 for plants, and 0 if netiher)
# Tested: Working
def recognize(image) -> tuple[str, int]:
    image.seek(0)

    image_bytes = image.getvalue()
    image = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)

    image = resize(image)
    response = client.models.generate_content(
        model = "gemini-2.0-flash",
        contents = [
            types.Part.from_bytes(data = image_bytes, mime_type = "image/jpeg"),
            "Do not include anything else but the format states, no greetings or extra details. Identify what if the following is a regular plant/vegetation, a wild animal, flower, pollinator or neither. Next, if it is either a plant or an animal, identify what type of plant or animal species it is and return that. If it is a plant, wild animal, pollinator, or flower, return 10 for pollinator, 5 for flower, 3 for wild animal, 1 for plant, or 0 if neither. The format should be \"Plant/Animal Species|1,3,5,or 10\". If it is neither plant nor animal then return None 0"
        ]
    )

    return response.text.split("|")[0], response.text.split("|")[1]



# ===== Testing Code: ======

# print(f"Current city: {user_location()}")

f = st.file_uploader("Image test", type = ["jpg", "jpeg", "png"])
if f:
    st.image(f, caption="Uploaded Image", use_container_width=True)
    species, points = recognize(f)
    if points == "1":
        st.write(f"You found the {species} species and are awarded {points} point!")
    else:
        st.write(f"You found the {species} species and are awarded {points} points!")