import streamlit as st
from datetime import datetime
from red_zones import load_zones_from_json, load_airports
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

# About Button
if st.button("ℹ️ About SafeTrip"):
    st.switch_page("1_About.py")

# Country coordinates (replacing geocoder)
country_coords = {
    "Afghanistan": (33.9391, 67.7100),
    "Armenia": (40.0691, 45.0382),
    "Azerbaijan": (40.1431, 47.5769),
    "Belarus": (53.7098, 27.9534),
    "Burkina Faso": (12.2383, -1.5616),
    "Ethiopia": (9.1450, 40.4897),
    "Gaza": (31.5018, 34.4663),
    "Iran": (32.4279, 53.6880),
    "Iraq": (33.3152, 44.3661),
    "Israel": (31.0461, 34.8516),
    "Lebanon": (33.8547, 35.8623),
    "Libya": (26.3351, 17.2283),
    "Mali": (17.5707, -3.9962),
    "Niger": (17.6078, 8.0817),
    "North Korea": (40.3399, 127.5101),
    "Russia": (61.5240, 105.3188),
    "Somalia": (5.1521, 46.1996),
    "South Sudan": (6.8770, 31.3070),
    "Sudan": (12.8628, 30.2176),
    "Syria": (34.8021, 38.9968),
    "Ukraine": (48.3794, 31.1656)
}

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

    for zone in red_zones:
        country = zone['country']
        if country not in country_coords:
            continue
        lat, lon = country_coords[country]
        point = Point(lon, lat)
        dist_route = point.distance(route_line) * 111  # Convert degrees to km
        dist_from = geodesic((lat, lon), from_coords).km
        dist_to = geodesic((lat, lon), to_coords).km
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
