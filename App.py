import streamlit as st
import geopandas as gpd
import pandas as pd
import rasterio
from rasterio.mask import mask

st.title("Rahuri Crop Recommendation App")

# Step 1: Upload shapefile/KML/KMZ
uploaded_file = st.file_uploader(
    "Upload shapefile (.zip with .shp, .shx, .dbf) or KML/KMZ",
    type=["zip", "kml", "kmz"]
)

# Step 2: Load crop database
crops = pd.read_csv("crop recomendation list.csv")

if uploaded_file:
    # Read shapefile
    if uploaded_file.name.endswith(".zip"):
        gdf = gpd.read_file(f"zip://{uploaded_file.name}")
    else:
        gdf = gpd.read_file(uploaded_file)

    st.write("Uploaded field(s):")
    st.map(gdf)

    # Step 3: Load raster maps
    salinity_raster = rasterio.open("Rasters/salinity classified.tif")
    slope_raster = rasterio.open("Rasters/slope classified.tif")
    suitability_raster = rasterio.open("Rasters/sutability.tif")

    results = []

    # Step 4: Loop through each field polygon
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
            'Field_ID': row.get('Name', f'Field_{idx}'),
            'Average_Salinity': round(sal_avg, 2),
            'Average_Slope': round(slope_avg, 2),
            'Average_Suitability': round(suit_avg, 2),
            'Recommended_Crops': ', '.join(recommended)
        })

    # Step 5: Display results
    results_df = pd.DataFrame(results)
    st.write("Crop Recommendation Results:")
    st.dataframe(results_df)

    # Step 6: Allow download as CSV
    csv = results_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Download CSV",
        data=csv,
        file_name='recommended_crops.csv',
        mime='text/csv'
    )
