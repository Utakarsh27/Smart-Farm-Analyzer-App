import streamlit as st
import geopandas as gpd
import pandas as pd
import rasterio
from rasterio.mask import mask
from shapely.geometry import Polygon

st.title("Rahuri Crop Recommendation App - Demo Version")

# -----------------------------
# Step 0: Define demo polygon(s)
# -----------------------------
demo_polygons = [Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])]  # Replace with any coordinates
gdf = gpd.GeoDataFrame({'Field_ID': ['Field_1'], 'geometry': demo_polygons})

st.write("Demo field(s):")
st.map(gdf)

# -----------------------------
# Step 1: Load crop database
# -----------------------------
# Make sure 'crop recommendation list.csv' is in the same folder
crops = pd.read_csv("crop recommendation list.csv")
st.write("Crop database preview:")
st.dataframe(crops.head())

# -----------------------------
# Step 2: Load raster maps
# -----------------------------
# Replace these with your actual raster file paths
salinity_raster = rasterio.open("Rasters/salinity_classified.tif")
slope_raster = rasterio.open("Rasters/slope_classified.tif")
suitability_raster = rasterio.open("Rasters/suitability.tif")

# -----------------------------
# Step 3: Loop through polygons
# -----------------------------
results = []

for idx, row in gdf.iterrows():
    geom = [row['geometry']]  # Must be a list for rasterio.mask

    # Extract raster values inside polygon
    sal_masked, _ = mask(salinity_raster, geom, crop=True)
    slope_masked, _ = mask(slope_raster, geom, crop=True)
    suit_masked, _ = mask(suitability_raster, geom, crop=True)

    # Calculate average values
    sal_avg = sal_masked.mean()
    slope_avg = slope_masked.mean()
    suit_avg = suit_masked.mean()

    # Recommend crops based on thresholds in CSV
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

# -----------------------------
# Step 4: Display results
# -----------------------------
results_df = pd.DataFrame(results)
st.write("Crop Recommendation Results:")
st.dataframe(results_df)

# -----------------------------
# Step 5: Download CSV
# -----------------------------
csv = results_df.to_csv(index=False).encode('utf-8')
st.download_button(
    "Download CSV",
    data=csv,
    file_name='recommended_crops_demo.csv',
    mime='text/csv'
)
