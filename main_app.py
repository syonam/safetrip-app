import streamlit as st
from datetime import datetime
from red_zones import load_zones_from_json, load_airports
from geopy.distance import geodesic
from shapely.geometry import Point, LineString
import openai
from openai import OpenAI
import pandas as pd

# Configure OpenAI
client = OpenAI(api_key=st.secrets["openai_api_key"])
# Page config
st.set_page_config(page_title="SafeTrip", layout="wide")

# Styling with background image, Roboto font, and transparent overlay
st.markdown(
    f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@700&display=swap');

        .stApp {{
            background: url("https://wallpapershome.com/images/pages/ico_h/26675.jpg") no-repeat center center fixed;
            background-size: cover;
            font-family: 'Roboto', sans-serif;
        }}

        .overlay-box {{
            background-color: rgba(255, 255, 255, 0.85);
            padding: 1.5rem;
            border-radius: 12px;
        }}

        h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, .stButton>button, .stSelectbox label {{
            font-weight: 700 !important;
            color: #000000 !important;
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

# App title
with st.container():
    st.markdown("""<div class='overlay-box'>""", unsafe_allow_html=True)
    st.markdown("<h1>SafeTrip – Fly Safer</h1>", unsafe_allow_html=True)
    st.markdown("##### Check your flight route and cities for any nearby conflict zones.")
    st.markdown("---")
    st.markdown("""</div>""", unsafe_allow_html=True)

# Static coordinates to avoid API calls
STATIC_COORDS = {
    "Iran": (32.4279, 53.6880),
    "Ukraine": (48.3794, 31.1656),
    "Russia": (61.5240, 105.3188),
    "Israel": (31.0461, 34.8516),
    "Gaza": (31.5018, 34.4663),
    "Afghanistan": (33.9391, 67.7100),
    "Lebanon": (33.8547, 35.8623),
    "Iraq": (33.3152, 44.3661),
    "Syria": (34.8021, 38.9968),
}

# Fetch coordinates using OpenAI
@st.cache_data
def fetch_country_coordinates(country):
    if country in STATIC_COORDS:
        return STATIC_COORDS[country]

    # Otherwise skip API call to conserve quota
    st.warning(f"No coordinates found for {country} and skipping API call to conserve usage.")
    return None, None

# Load airport and airline data
@st.cache_data
def get_airport_options():
    return load_airports()

@st.cache_data
def load_airlines():
    url = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airlines.dat"
    cols = ["Airline ID", "Name", "Alias", "IATA", "ICAO", "Callsign", "Country", "Active"]
    df = pd.read_csv(url, names=cols, header=None)
    df = df[df["Active"] == "Y"]
    airline_list = sorted(df["Name"].dropna().unique().tolist())
    return airline_list

airports = get_airport_options()
airline_list = load_airlines()

# UI inputs
with st.container():
    st.markdown("""<div class='overlay-box'>""", unsafe_allow_html=True)
    from_city = st.selectbox("From (City)", options=airports.keys(), index=0)
    to_city = st.selectbox("To (City)", options=airports.keys(), index=1)
    airline = st.selectbox("Airline", options=airline_list)
    date = st.date_input("Date of Travel", datetime.today())
    st.markdown("""</div>""", unsafe_allow_html=True)

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
