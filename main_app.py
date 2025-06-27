import streamlit as st
from datetime import datetime
from red_zones import load_zones_from_json, load_airports
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from shapely.geometry import Point, LineString

# Streamlit Config
st.set_page_config(page_title="SafeTrip", layout="centered")

# Style
st.markdown("""
    <style>
        body, .main, .block-container {
            background-color: #cce5ff;
        }
        .scroll-box {
            max-height: 200px;
            overflow-y: auto;
            padding: 10px;
            border: 1px solid #ccc;
            background-color: white;
            border-radius: 8px;
        }
    </style>
""", unsafe_allow_html=True)

# Logo and Title
st.image("logo.png", width=200)
st.title("✈️ SafeTrip – Fly Safer")
st.markdown("##### Check your flight route and cities for any nearby conflict zones.")
st.markdown("---")

# About Button (fixed)
if st.button("ℹ️ About SafeTrip"):
    st.switch_page("1_About.py")

# Load airports
@st.cache_data
def get_airport_options():
    return load_airports()

airports = get_airport_options()

# UI Elements
from_city = st.selectbox("From (City)", options=airports.keys(), index=0)
to_city = st.selectbox("To (City)", options=airports.keys(), index=1)
airline = st.selectbox("Airline", options=["IndiGo", "Air India", "Emirates", "Lufthansa", "Qatar Airways", "Other"])
date = st.date_input("Date of Travel", datetime.today())

# Submit Button
if st.button("Check Route Safety ✈️"):
    from_coords = (airports[from_city]['latitude_deg'], airports[from_city]['longitude_deg'])
    to_coords = (airports[to_city]['latitude_deg'], airports[to_city]['longitude_deg'])
    red_zones = load_zones_from_json()

    route_line = LineString([from_coords[::-1], to_coords[::-1]])
    risky_zones = []

    geolocator = Nominatim(user_agent="safetrip-app")

    for zone in red_zones:
        loc = geolocator.geocode(zone['country'])
        if not loc:
            continue
        point = Point(loc.longitude, loc.latitude)
        dist_route = point.distance(route_line) * 111  # Convert degrees to km
        dist_from = geodesic((loc.latitude, loc.longitude), from_coords).km
        dist_to = geodesic((loc.latitude, loc.longitude), to_coords).km
        if min(dist_route, dist_from, dist_to) <= 500:
            zone['distance_km'] = round(min(dist_route, dist_from, dist_to), 1)
            risky_zones.append(zone)

    st.markdown("---")
    if not risky_zones:
        st.success("✅ Your route and cities appear safe from nearby conflict zones.")
    else:
        st.error(f"⚠️ Your flight passes near {len(risky_zones)} conflict zones:")
        for zone in risky_zones:
            st.markdown(f"**{zone['country']}** *(~{zone['distance_km']} km away)*")
            st.markdown(f"""<div class='scroll-box'>{zone['alert'][:1500]}</div>""", unsafe_allow_html=True)
