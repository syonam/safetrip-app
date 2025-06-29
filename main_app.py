import streamlit as st
from datetime import datetime
from red_zones import load_zones_from_json, load_airports
from geopy.distance import geodesic
from shapely.geometry import Point, LineString
import openai

# Configure OpenAI
openai.api_key = st.secrets["openai_api_key"]

# Page config
st.set_page_config(page_title="SafeTrip", layout="wide")

# Background styling using hosted plane image
st.markdown(
    f"""
    <style>
        .stApp {{
            background: url("https://images.unsplash.com/photo-1504197885-609741792ce7?auto=format&fit=crop&w=1650&q=80") no-repeat center center fixed;
            background-size: cover;
        }}
        .main-title h1 {{
            color: black !important;
        }}
        .scroll-box {{
            max-height: 200px;
            overflow-y: auto;
            padding: 10px;
            border: 1px solid #ccc;
            background-color: rgba(255, 255, 255, 0.85);
            border-radius: 8px;
            color: black;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

# Logo and title
col1, col2 = st.columns([1, 10])
with col1:
    st.image("black_circle_360x360.png", width=70)
with col2:
    st.markdown("<h1 class='main-title'>SafeTrip – Fly Safer</h1>", unsafe_allow_html=True)

st.markdown("##### Check your flight route and cities for any nearby conflict zones.")
st.markdown("---")

# Fetch coordinates using OpenAI
@st.cache_data
def fetch_country_coordinates(country_name):
    try:
        prompt = f"What are the latitude and longitude coordinates of {country_name}?"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content
        parts = content.replace("°", "").replace(",", "").split()
        lat = float([p for p in parts if p.replace('.', '', 1).isdigit()][0])
        lon = float([p for p in parts if p.replace('.', '', 1).isdigit()][1])
        return lat, lon
    except Exception as e:
        st.warning(f"Could not fetch coordinates for {country_name}: {e}")
        return None, None

# Load airport data
@st.cache_data
def get_airport_options():
    return load_airports()

airports = get_airport_options()

# UI inputs
from_city = st.selectbox("From (City)", options=airports.keys(), index=0)
to_city = st.selectbox("To (City)", options=airports.keys(), index=1)
airline = st.selectbox("Airline", options=["IndiGo", "Air India", "Emirates", "Lufthansa", "Qatar Airways", "Other"])
date = st.date_input("Date of Travel", datetime.today())

# Check Route button
if st.button("Check Route Safety ✈️"):
    from_coords = (airports[from_city]['latitude_deg'], airports[from_city]['longitude_deg'])
    to_coords = (airports[to_city]['latitude_deg'], airports[to_city]['longitude_deg'])
    red_zones = load_zones_from_json()

    route_line = LineString([from_coords[::-1], to_coords[::-1]])
    risky_zones = []

    for zone in red_zones:
        country = zone['country']
        lat, lon = fetch_country_coordinates(country)
        if not lat or not lon:
            continue
        point = Point(lon, lat)
        dist_route = point.distance(route_line) * 111
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
