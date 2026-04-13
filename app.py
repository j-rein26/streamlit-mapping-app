import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium



# ----- Soft Login -----


def soft_login():
    if "user_name" not in st.session_state:
        st.session_state.user_name = None

    if st.session_state.user_name is None:
        st.title("Welcome 👋")

        name = st.text_input("Enter your name to continue:")

        if st.button("Continue"):
            if name.strip():
                st.session_state.user_name = name.strip()
                st.rerun()
            else:
                st.warning("Please enter a name.")
        st.stop()

    return st.session_state.user_name

# ----- END Soft Login -----
user_name = soft_login()
st.sidebar.success(f"Logged in as: {user_name}")

# 🔥 Set default filter ONCE
if "visited_filter" not in st.session_state:
    st.session_state.visited_filter = user_name


st.title("Address Map Viewer")

# -------------------------
# 1. CONFIGURE MONTHS HERE
# -------------------------

SPREADSHEET_ID = st.secrets["Spreadsheet_id"]

MONTH_SHEETS = {
                
    "March": 1840533139, # Replace with actual gid
}

# -------------------------
# 2. MONTH SELECTOR
# -------------------------
st.sidebar.header("Select Month")
selected_month = st.sidebar.selectbox("Month", list(MONTH_SHEETS.keys()))

gid = MONTH_SHEETS[selected_month]

# Build CSV export link
sheet_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&gid={gid}"

# -------------------------
# 3. LOAD DATA
# -------------------------
df = pd.read_csv(sheet_url)

# 🔥 Clean whitespace
df = df.apply(lambda col: col.astype(str).str.strip() if col.dtype == "object" else col)

# 🔥 Remove empty rows (Google Sheets often exports these)
df = df.dropna(how="all")

# 🔥 Remove rows where Address is blank
df = df[df["Address"].notna() & (df["Address"].str.strip() != "")]


# Drop duplicate addresses
df = df.drop_duplicates(subset=["Address", "City", "State", "Zip"])

# Ensure numeric types
df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
df = df.dropna(subset=["Latitude", "Longitude"])

# -------------------------
# 4. SIDEBAR FILTERS
# -------------------------
st.sidebar.header("Filters")

cities = sorted(df["City"].dropna().unique())

selected_city = st.sidebar.multiselect("City", cities, default=cities)

filtered = df[df["City"].isin(selected_city)]

# Build a list of unique visitors
visitor_names = sorted(
    [v for v in df["Visited By"].dropna().unique() if str(v).strip() != ""]
)

options = ["All", "Not Visited"] + visitor_names

visited_choice = st.sidebar.selectbox(
    "Visited?",
    options,
    index=options.index(st.session_state.visited_filter)
    if st.session_state.visited_filter in options else 0,
    key="visited_filter"
)


if visited_choice == "Not Visited":
    filtered = filtered[
        filtered["Visited By"].isna() |
        (filtered["Visited By"].str.strip() == "")
    ]
elif visited_choice != "All":
    filtered = filtered[
        filtered["Visited By"].str.strip() == visited_choice
    ]

if st.sidebar.button("Show All"):
    st.session_state.visited_filter = "All"
    st.rerun()

# -------------------------
# 5. CREATE MAP
# -------------------------
if filtered.empty:
    st.warning("No addresses match your filters.")
else:
    avg_lat = filtered["Latitude"].mean()
    avg_lon = filtered["Longitude"].mean()

    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=11)

    for _, row in filtered.iterrows():
        address = f"{row['Address']}, {row['City']}, {row['State']} {row['Zip']}"
        maps_link = f"https://www.google.com/maps/dir/?api=1&destination={row['Latitude']},{row['Longitude']}"

        popup = f"""
        <b>{row['First']} {row['Last']}</b><br>
        {address}<br><br>
        <a href="{maps_link}" target="_blank" style="font-size:16px;">
        🚗 Open in Maps
        </a>
        """
        folium.Marker(
            [row["Latitude"], row["Longitude"]],
            popup=popup,
            tooltip=row["Last"]
        ).add_to(m)

    st_folium(m, width=700, height=500)


