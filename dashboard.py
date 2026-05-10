import streamlit as st
from homeharvest import scrape_property
import pandas as pd
from datetime import datetime

current_year = datetime.now().year

st.set_page_config(page_title="Property Dashboard", layout="wide")
st.title("🏠 Property Data Dashboard")

# --- Sidebar filters ---
st.sidebar.header("Search Filters")

location = st.sidebar.text_input("Location", value="Atlanta, GA")

listing_type = st.sidebar.selectbox(
    "Listing Type",
    ["sold", "for_sale", "for_rent", "pending"]
)

property_type = st.sidebar.multiselect(
    "Property Type",
    ["single_family", "multi_family", "condos", "townhomes", "duplex_triplex"],
    default=["single_family"]
)

use_radius = st.sidebar.checkbox("Search by radius (enter a full address above)")
radius = None
if use_radius:
    radius = st.sidebar.slider("Radius (miles)", 1, 25, 5)

past_days = st.sidebar.slider("Days of history", 7, 365, 30)

st.sidebar.subheader("Price Range")
price_min = st.sidebar.number_input("Min Price ($)", value=0, step=10000, format="%d")
price_max = st.sidebar.number_input("Max Price ($)", value=500000, step=10000, format="%d")

beds_range = st.sidebar.slider("Bedrooms", min_value=0, max_value=10, value=(0, 10))
baths_range = st.sidebar.slider("Bathrooms", min_value=0, max_value=10, value=(0, 10))
sqft_range = st.sidebar.slider("Square Footage", min_value=0, max_value=10000, value=(0, 10000), step=100)
year_range = st.sidebar.slider("Year Built", min_value=1900, max_value=current_year, value=(1900, current_year))

# --- Pull data ---
if st.button("🔍 Pull Data"):
    with st.spinner("Fetching properties..."):
        try:
            props = scrape_property(
                location=location,
                listing_type=listing_type,
                property_type=property_type if property_type else None,
                past_days=past_days,
                price_min=price_min if price_min > 0 else None,
                price_max=price_max if price_max > 0 else None,
                beds_min=beds_range[0] if beds_range[0] > 0 else None,
                beds_max=beds_range[1] if beds_range[1] < 10 else None,
                baths_min=baths_range[0] if baths_range[0] > 0 else None,
                baths_max=baths_range[1] if baths_range[1] < 10 else None,
                sqft_min=sqft_range[0] if sqft_range[0] > 0 else None,
                sqft_max=sqft_range[1] if sqft_range[1] < 10000 else None,
                year_built_min=year_range[0] if year_range[0] > 1900 else None,
                year_built_max=year_range[1] if year_range[1] < current_year else None,
                radius=radius
            )

            if props.empty:
                st.warning("No properties found. Try adjusting your filters.")
            else:
                st.success(f"Found {len(props)} properties")

                # --- Summary stats ---
                st.subheader("📊 Summary")
                col1, col2, col3, col4 = st.columns(4)

                price_col = "list_price"
                if price_col in props.columns:
                    col1.metric("Avg Price", f"${props[price_col].mean():,.0f}")
                    col2.metric("Median Price", f"${props[price_col].median():,.0f}")

                if "price_per_sqft" in props.columns:
                    col3.metric("Avg Price/SqFt", f"${props['price_per_sqft'].mean():,.0f}")

                if "days_on_mls" in props.columns:
                    col4.metric("Avg Days on Market", f"{props['days_on_mls'].mean():,.0f}")

                # --- Map ---
                if "latitude" in props.columns and "longitude" in props.columns:
                    map_data = props[["latitude", "longitude"]].dropna()
                    if not map_data.empty:
                        st.subheader("🗺️ Map")
                        st.map(map_data)

                # --- Table ---
                st.subheader("📋 Results")

                display_cols = [
                    "street", "city", "state", "zip_code",
                    "list_price", "sold_price", "beds", "full_baths",
                    "sqft", "price_per_sqft", "days_on_mls",
                    "year_built", "style", "status"
                ]
                available_cols = [c for c in display_cols if c in props.columns]
                st.dataframe(props[available_cols], use_container_width=True)

                # --- Download ---
                csv = props.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="⬇️ Download Full CSV",
                    data=csv,
                    file_name="properties.csv",
                    mime="text/csv"
                )

        except Exception as e:
            st.error(f"Something went wrong: {e}")