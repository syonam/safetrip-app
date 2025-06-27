import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import pandas as pd


def scrape_conflict_zones():
    url = "https://safeairspace.net/summary/"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    zone_blocks = soup.select("div.summary-main-warning")
    print(f"✅ Found {len(zone_blocks)} red zone entries")

    red_zones = []

    for block in zone_blocks:
        country = block.get("data-feed-item-country") or block.select_one(".summary-main-warning-name").text.strip()

        content_div = block.select_one(".summary-main-warning-content")
        if not content_div:
            continue

        alert_text = content_div.get_text(separator="\n", strip=True)

        red_zones.append({
            "region": "Unknown",
            "country": country,
            "alert": alert_text,
            "severity": "High",
            "coordinates": None,
            "radius_km": 300,
            "source": url,
            "last_updated": datetime.utcnow().isoformat()
        })

    return red_zones

def save_to_json(data, filename="red_zones.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_zones_from_json(filename="red_zones.json"):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def load_airports():
    df = pd.read_csv("airports.csv")  # Local file now
    df = df[df['type'].isin(['large_airport', 'medium_airport'])]
    df['label'] = df['municipality'].fillna(df['name']) + " - " + df['iso_country']
    df = df.dropna(subset=['latitude_deg', 'longitude_deg'])
    df = df[~df['label'].duplicated()]
    return df[['label', 'latitude_deg', 'longitude_deg']].set_index('label').to_dict('index')

if __name__ == "__main__":
    zones = scrape_conflict_zones()
    save_to_json(zones)
    print(f"✅ Saved {len(zones)} red zones to red_zones.json")