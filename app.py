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
SUPABASE_KEY = "sb_secret_Hg_vcloiHhea1BqF4jUY6g_hEsAcIpF"  # backend key ONLY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
faker = Faker("en_IN")

# ---------------- LOGIN ----------------
st.set_page_config(page_title="SAAT Dashboard", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("🔐 SAAT Internal Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == "admin" and password == "admin123":
            st.session_state.logged_in = True
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")

if not st.session_state.logged_in:
    login()
    st.stop()

# ---------------- HELPERS ----------------
def generate_lead():
    name = faker.name()
    lead_type = random.choice(["Buy", "Rent", "Sell"])
    location = random.choice([
        "Kolkata", "Salt Lake", "New Town", "Rajarhat",
        "Howrah", "Bangalore", "Mumbai", "Pune"
    ])
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
    data = supabase.table("leads") \
        .select("*") \
        .order("created_at", desc=True) \
        .execute()
    return pd.DataFrame(data.data)

# ---------------- UI HEADER ----------------
col1, col2 = st.columns([6, 1])

with col1:
    st.markdown("## 📊 SAAT Leads Dashboard")

with col2:
    if st.button("🔴 LIVE"):
        for _ in range(3):   # generate 3 leads per click
            generate_lead()
        st.success("Live data generated")

# ---------------- DATA ----------------
df = fetch_leads()

if df.empty:
    st.warning("No leads yet.")
    st.stop()

# ---------------- FILTERS ----------------
f1, f2 = st.columns(2)

with f1:
    type_filter = st.selectbox("Filter Type", ["All", "Buy", "Rent", "Sell"])

with f2:
    search = st.text_input("Search (name / phone / location)")

if type_filter != "All":
    df = df[df["type"] == type_filter]

if search:
    df = df[df.apply(lambda r: search.lower() in str(r.values).lower(), axis=1)]

# ---------------- TABLE ----------------
st.dataframe(
    df[[
        "name", "type", "phone", "email",
        "location", "budget", "search_message", "created_at"
    ]],
    use_container_width=True
)

# ---------------- MAP ----------------
st.markdown("## 🌍 Property Map (Demo)")

map_center = [20.5937, 78.9629]  # India
m = folium.Map(location=map_center, zoom_start=4)

for _, row in df.head(20).iterrows():
    folium.Marker(
        location=map_center,
        popup=f"{row['name']} – {row['location']}",
        icon=folium.Icon(color="blue")
    ).add_to(m)

st_folium(m, height=400)
