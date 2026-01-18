import streamlit as st
from supabase import create_client
from faker import Faker
import pandas as pd
import random
import folium
from streamlit_folium import st_folium
from datetime import datetime

# --- TEMP TIME DEBUG (ADD HERE) ---
st.subheader("🧪 Time Debug (Temporary)")

utc_time = pd.Timestamp.utcnow()  # already UTC-aware
india_time = utc_time.tz_convert("Asia/Kolkata")

st.write("SERVER TIME (UTC):", utc_time)
st.write("INDIA TIME:", india_time)

st.divider()
# --- END DEBUG ---
# ---------------- CONFIG ----------------
SUPABASE_URL = "https://ivtjnwuhjtihosutpmss.supabase.co"
SUPABASE_KEY = "sb_secret_Hg_vcloiHhea1BqF4jUY6g_hEsAcIpF"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
faker = Faker("en_IN")

CITY_COORDS = {
    "Kolkata": (22.5726, 88.3639),
    "Salt Lake": (22.5867, 88.4171),
    "New Town": (22.5800, 88.4700),
    "Howrah": (22.5958, 88.2636),
    "Mumbai": (19.0760, 72.8777),
    "Bangalore": (12.9716, 77.5946),
    "Pune": (18.5204, 73.8567),
}

# ---------------- PAGE ----------------
st.set_page_config(page_title="SAAT Dashboard", layout="wide")

# ---------------- LOGIN ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("🔐 SAAT Internal Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u == "admin" and p == "admin123":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Invalid credentials")

if not st.session_state.logged_in:
    login()
    st.stop()

# ---------------- DATA HELPERS ----------------
def generate_lead():
    name = faker.name()
    lead_type = random.choice(["Buy", "Rent", "Sell"])
    location = random.choice(list(CITY_COORDS.keys()))
    phone = "9" + str(random.randint(100000000, 999999999))
    email = name.lower().replace(" ", ".") + "@gmail.com"
    budget = f"{random.randint(20, 90)} lakh"

    search_message = f"{name} searched for 2BHK flat near {location} around {budget}"

    supabase.table("leads").insert({
        "name": name,
        "type": lead_type,
        "phone": phone,
        "email": email,
        "location": location,
        "budget": budget,
        "search_message": search_message,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

def fetch_leads():
    res = supabase.table("leads") \
        .select("*") \
        .order("created_at", desc=True) \
        .execute()
    return pd.DataFrame(res.data)

# ---------------- HEADER ----------------
c1, c2 = st.columns([6, 1])

with c1:
    st.markdown("## 📊 SAAT Leads Dashboard")

with c2:
    if st.button("🔴 LIVE"):
        for _ in range(2):
            generate_lead()
        st.success("Live data generated")

# ---------------- LOAD DATA ----------------
df = fetch_leads()

if df.empty:
    st.warning("No leads found.")
    st.stop()

df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime("%d %b %Y • %I:%M %p")

# ---------------- FILTER ----------------
type_filter = st.selectbox("Filter Type", ["All", "Buy", "Rent", "Sell"])
if type_filter != "All":
    df = df[df["type"] == type_filter]

# ---------------- TABLE ----------------
st.dataframe(
    df[[
        "name", "type", "phone", "email",
        "location", "budget", "search_message", "created_at"
    ]],
    use_container_width=True
)

# ---------------- MAP PER PERSON ----------------
st.markdown("## 🌍 Lead Location Map")

selected_name = st.selectbox(
    "Select Lead",
    df["name"].tolist()
)

selected_row = df[df["name"] == selected_name].iloc[0]
city = selected_row["location"]
coords = CITY_COORDS.get(city, (20.5937, 78.9629))

m = folium.Map(location=coords, zoom_start=11)
folium.Marker(
    location=coords,
    popup=f"{selected_row['name']} – {city}",
    icon=folium.Icon(color="blue")
).add_to(m)

st_folium(m, height=420)
