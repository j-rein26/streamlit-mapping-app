import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium



# ----- SECURE PASSWORD PROTECTION (uses Streamlit Secrets) -----

def check_password():
    """Returns True if the user entered the correct password."""

    # The password is stored securely in Streamlit Cloud → Settings → Secrets
    correct_password = st.secrets["app_password"]

    def password_entered():
        # Check whether entered password is correct
        if st.session_state["password"] == correct_password:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password
        else:
            st.session_state["password_correct"] = False

    # First run, show password input
    if "password_correct" not in st.session_state:
        st.text_input("Enter password:", type="password",
                      on_change=password_entered, key="password")
        return False

    # Password is wrong
    elif not st.session_state["password_correct"]:
        st.text_input("Enter password:", type="password",
                      on_change=password_entered, key="password")
        st.error("Incorrect password")
        return False

    # Password is correct
    else:
        return True

if not check_password():
    st.stop()

# ----- END PASSWORD PROTECTION -----



st.title("Address Map Viewer")

# -------------------------
# 1. CONFIGURE MONTHS HERE
# -------------------------

SPREADSHEET_ID = st.secrets["Spreadsheet_id"]

MONTH_SHEETS = {
    "September": 0,            # Replace with actual gid
    "October": 1547489573,           # Replace with actual gid
    "November": 1968577955            # Replace with actual gid
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

visited_choice = st.sidebar.selectbox(
    "Visited?",
    ["All", "Not Visited"] + visitor_names
)


if visited_choice == "Not Visited":
    filtered = filtered[filtered["Visited By"].isna() | (filtered["Visited By"].str.strip() == "")]
elif visited_choice != "All":
    # Show only locations visited by the selected person
    filtered = filtered[filtered["Visited By"].str.contains(visited_choice, na=False)]


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
        popup = f"""
        {row['First']} {row['Last']}<br>
        {row['Address']}<br>
        {row['City']}, {row['State']} {row['Zip']}
        """
        folium.Marker(
            [row["Latitude"], row["Longitude"]],
            popup=popup,
            tooltip=row["Last"]
        ).add_to(m)

    st_folium(m, width=700, height=500)


