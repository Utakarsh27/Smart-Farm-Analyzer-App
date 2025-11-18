import streamlit as st
import geopandas as gpd
import pandas as pd
import rasterio
from rasterio.mask import mask
from shapely.geometry import Polygon
from zipfile import ZipFile
import io

st.title("Rahuri Crop Recommendation App 🌱")

# -------------------------------
# Step 1: Upload shapefile/KML/KMZ (optional)
uploaded_file = st.file_uploader(
    "Upload shapefile (.zip) or KML/KMZ (optional, else sample polygons will be used)",
    type=["zip", "kml", "kmz"]
)

# -------------------------------
# Step 2: Load or create GeoDataFrame
if uploaded_file:
    try:
        if uploaded_file.name.endswith(".zip"):
            gdf = gpd.read_file(f"zip://{uploaded_file.name}")
        else:
            # KML/KMZ support (may need driver)
            gdf = gpd.read_file(uploaded_file)
        st.success("Shapefile/KML loaded successfully!")
    except Exception as e:
        st.warning(f"Error reading file: {e}. Using sample polygons instead.")
        uploaded_file = None

if not uploaded_file:
    st.info("Using sample polygons for demo.")
    polygons = [
        Polygon([(72.8,19.9),(72.8,20.0),(72.9,20.0),(72.9,19.9)]),
        Polygon([(72.85,19.95),(72.85,20.05),(72.95,20.05),(72.95,19.95)])
    ]
    gdf = gpd.GeoDataFrame({'Field_ID': ['Field_1','Field_2']}, geometry=polygons)

st.write("Fields:")
st.map(gdf)

# -------------------------------
# Step 3: Load crop database
crops = pd.read_csv("crop recomendation list.csv")
st.write("Crop Database:")
st.dataframe(crops)

# -------------------------------
# Step 4: Load raster files
salinity_raster = rasterio.open("Rasters/salinity classified.tif")
slope_raster = rasterio.open("Rasters/slope classified.tif")
suitability_raster = rasterio.open("Rasters/sutability.tif")

# -------------------------------
# Step 5: Crop recommendation logic
results = []

for idx, row in gdf.iterrows():
    geom = [row['geometry']]  # geometry must be a list

    # Extract raster values within polygon
    sal_masked, _ = mask(salinity_raster, geom, crop=True)
    slope_masked, _ = mask(slope_raster, geom, crop=True)
    suit_masked, _ = mask(suitability_raster, geom, crop=True)

    # Calculate average values
    sal_avg = sal_masked.mean()
    slope_avg = slope_masked.mean()
    suit_avg = suit_masked.mean()

    # Recommend crops
    recommended = []
    for _, crop in crops.iterrows():
        if sal_avg <= crop['EC_max'] and slope_avg <= crop['Slope_max']:
            recommended.append(crop['Crop'])

    results.append({
        'Field_ID': row['Field_ID'],
        'Average_Salinity': round(sal_avg, 2),
        'Average_Slope': round(slope_avg, 2),
        'Average_Suitability': round(suit_avg, 2),
        'Recommended_Crops': ', '.join(recommended)
    })

results_df = pd.DataFrame(results)
st.write("Crop Recommendation Results:")
st.dataframe(results_df)

# -------------------------------
# Step 6: Download CSV
csv = results_df.to_csv(index=False).encode('utf-8')
st.download_button(
    "Download CSV",
    data=csv,
    file_name='recommended_crops.csv',
    mime='text/csv'
)
