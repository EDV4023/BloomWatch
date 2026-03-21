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
import requests

client = genai.Client(api_key = st.secrets.API_KEY)

# Prevent user from bypassing authentication
if "loggedin" not in st.session_state:
    st.switch_page(r"Homepage.py")

#Tested: Working
def resize(image):
    max_side = 1200
    height, width = image.shape[0:2]
    scale = max_side / max(height, width)

    if scale < 1:
        image = cv2.resize(image, (int(scale*width),int(scale*height)))
    return image    

# # Tested: Working
# def get_latlng() -> tuple[float, float]:
#     g = geocoder.ip("me") # Get user's current IP: Need to ask user for permission to access location data

#     # If latitude and longitude attribute exsits then extract location data
#     if g.latlng:
#         lat, long = g.latlng
#         return lat, long
#     else:
#         return None

# # Tested: Working
# def convert_latlng_to_city(lat: float, long: float) -> tuple[str, str] | None:
#     geolocator = Nominatim(user_agent = "backyard_environmental_diversity_checker | edanvaiz@gmail.com")

#     try:
#         location = geolocator.reverse(f"{lat},{long}")

#         # Obtain postal code/zip code
#         if location and "address" in location.raw:
#             address = location.raw["address"]
#             return address["town"], address["state"]
#         return None
#     except (GeocoderTimedOut, GeocoderServiceError):
#         return None

# Tested: Working
def user_location() -> tuple[str, str] | None:
    users_ref = db.reference(f"users/{st.session_state.username}")
    users_dict = users_ref.get()
    if users_dict:
        return users_dict["city"], users_dict["state"]
    else:
        return None
    
    

# Recognized image to be plant, animal, or neither and assigns points (10 for pollinators, 5 for flowers, 3 for animals, 1 for plants, and 0 if netiher)
# Tested: Working
def recognize(image, city, state) -> tuple[str, int]:
    image.seek(0)

    image_bytes = image.getvalue()
    image = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)

    image = resize(image)
    response = client.models.generate_content(
        model = "gemini-2.0-flash",
        contents = [
            types.Part.from_bytes(data = image_bytes, mime_type = "image/jpeg"),
            f'''
Task: Regional Ecological Identification
Location: {city}, {state}, USA

Instructions:
1. Identify the species in the image (Common name).
2. Determine if the species is indigenous to the specific ecosystem of {city}, {state}. 
   - If it was introduced from another continent or region and only if it disrupts the local environment, it is ok if it is harmless such as house plants for showcase (e.g., Chinese Tallow, Emerald Ash Borer, Kudzu), it MUST be classified as "Non-Native" with a score of -1.
3. Apply the following hierarchy for the score:
   - Non-native/Invasive = -1
   - Neither plant nor animal = 0
   - Regular plant/vegetation (non-flowering) = 1
   - Wild animal (non-pollinator) = 3
   - Flowering plant = 5
   - Pollinator = 10

Constraint: Do not include greetings, explanations, or Markdown formatting. 

Output Format: 
Native or Non-Native||Common Name||Score

If neither: "None||None||0"'''
        ]
    )

    return response.text.split("||")[0], response.text.split("||")[1], response.text.split("||")[2]

# Tested: Working
def identify(img):
    city, state = user_location()
    native, species, points = recognize(img,city,state)
    
    # ======== Testing Code (Comment out when deployed) ========= 
    # st.write(native)
    # st.write(species)
    # st.write(points)
    # st.write(city)
    # st.write(state)
    # ======== End of Testing Code =======

    points = int(points)
    users_ref = db.reference(f"users/{st.session_state.username}")
    users_dict = users_ref.get()
    species_list = users_dict["plants"] + users_dict["animals"] + users_dict["flowers"] + users_dict["pollinators"]

    match points:
        case -1:
            st.session_state.points -= 1
            st.warning(f"You found the **{species}** species and lost 1 point. This species is non-native to your environment, please remove this species from your backyard.")
            users_dict["non_native"].append(species)
            users_dict["points"] += -1
            users_ref.update({"non_native":users_dict["non_native"],"points":users_dict["points"]})
        case 0:
            st.info("This is not a new unique species.")
        case 1:
            if species in species_list:
                st.success(f"You found the **{species}** species (Type: Regular Plant)! No points were gained since this is not a new species")
                users_dict["plants"].append(species)
                users_ref.update({"plants":users_dict["plants"]})
                return
            st.session_state.points += 1
            st.success(f"You found the **{species}** species (Type: Regular Plant) and gained **{points}** points!")
            users_dict["plants"].append(species)
            users_dict["points"] += 1
            users_ref.update({"plants":users_dict["plants"],"points":users_dict["points"]})

        case 3:
            if species in species_list:
                st.success(f"You found the **{species}** species (Type: Regular Animal)! No points were gained since this is not a new species")
                users_dict["animals"].append(species)
                users_ref.update({"animals":users_dict["animals"]})
                return
            st.session_state.points += 3
            st.success(f"You found the **{species}** species (Type: Regular Animal) and gained **{points}** points!")
            users_dict["animals"].append(species)
            users_dict["points"] += 3
            users_ref.update({"animals":users_dict["animals"],"points":users_dict["points"]})

        case 5:
            if species in species_list:
                st.success(f"You found the **{species}** species (Type: Flower)! No points were gained since this is not a new species")
                users_dict["flowers"].append(species)
                users_ref.update({"flowers":users_dict["flowers"]})
                return
            st.session_state.points += 5
            st.success(f"You found the **{species}** species (Type: Flower) and gained **{points}** points!")
            users_dict["flowers"].append(species)
            users_dict["points"] += 5
            users_ref.update({"flowers": users_dict["flowers"],"points":users_dict["points"]})

        case 10:
            if species in species_list:
                st.success(f"You found the **{species}** species (Type: Pollinator)! No points were gained since this is not a new species")
                users_dict["pollinators"].append(species)
                users_ref.update({"pollinators":users_dict["pollinators"]})
                return
            st.session_state.points += 10
            st.success(f"You found the **{species}** species (Type: Pollinator) and gained **{points}** points!")
            users_dict["pollinators"].append(species)
            users_dict["points"] += 10
            users_ref.update({"pollinators": users_dict["pollinators"],"points":users_dict["points"]})


    st.session_state.history.append({
        "species":species,
        "points":points
    })
st.title(":green[Wildlife] Scan")

img = st.camera_input("Take an image of wildlife in you backyard")  # # Use when deployed
# img = st.file_uploader("Test Image")

if img:
    st.image(img)

if st.button("Identify", type = "primary") and img:
    identify(img)
