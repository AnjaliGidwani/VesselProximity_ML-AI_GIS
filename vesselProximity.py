import numpy as np
import pandas as pd
from haversine import haversine_vector, Unit
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point

# Load the CSV data 
data = pd.read_csv('D:\\GIS\\sample_data.csv')

# Define threshold distance for vessel proximity in kilometers
threshold_distance = 5 

# Calculate vessel proximity
def calculate_vessel_proximity(data, threshold_distance, lat_col='lat', lon_col='lon'):
    proximity_events = []
    error_rows = [] 
    
    # GeoDataFrame
    geometry = [Point(xy) for xy in zip(data[lon_col], data[lat_col])]
    gdf = gpd.GeoDataFrame(data, geometry=geometry)
    
    # Calculate all pairwise distances in combination mode
    all_positions = gdf[[lat_col, lon_col]].values
    distances_matrix = haversine_vector(all_positions, all_positions, Unit.KILOMETERS, comb=True).reshape(len(gdf), len(gdf))
    
    # Iterate through each vessel
    for i, row in gdf.iterrows():
        try:
            current_mmsi = row['mmsi']
            current_timestamp = row['timestamp']
        
            # distances for the current vessel
            distances = distances_matrix[i]
        
            # vessels within the threshold distance
            nearby_vessels = gdf[(distances < threshold_distance) & (gdf['mmsi'] != current_mmsi)]
        
            # Append the proximity event to the list
            if not nearby_vessels.empty:
                proximity_events.append({'mmsi': current_mmsi, 'vessel_proximity': nearby_vessels['mmsi'].tolist(), 
                'timestamp': current_timestamp})
        except Exception as e:
            # Log the error and continue
            error_rows.append({'index': i, 'error': str(e)})

    # DataFrame from the proximity events list
    proximity_df = pd.DataFrame(proximity_events)
    
    if error_rows:
        error_df = pd.DataFrame(error_rows)
        error_df.to_csv('D:\\GIS\\proximity_error_log.csv', index=False)

    return proximity_df


# calculate vessel proximity events
proximity_data = calculate_vessel_proximity(data, threshold_distance)

# output DataFrame
print(proximity_data)

# Export to a new CSV file
proximity_data.to_csv('D:\\GIS\\vessel_proximity_events.csv', index=False)

# Visualization
def visualize_proximity_events(data, proximity_data, lat_col='lat', lon_col='lon'):
    # GeoDataFrame from the original data
    geometry = [Point(xy) for xy in zip(data[lon_col], data[lat_col])]
    gdf = gpd.GeoDataFrame(data, geometry=geometry)
    
    # base map with vessel positions
    fig, ax = plt.subplots(1, 1, figsize=(15, 15))
    gdf.plot(ax=ax, color='blue', markersize=5, label='Vessel Position')
    
    # proximity events to the plot
    for index, event in proximity_data.iterrows():
        vessel = gdf[gdf['mmsi'] == event['mmsi']]
        for mmsi in event['vessel_proximity']:
            nearby_vessel = gdf[gdf['mmsi'] == mmsi]
            ax.plot([vessel.geometry.x.values[0], nearby_vessel.geometry.x.values[0]], 
                    [vessel.geometry.y.values[0], nearby_vessel.geometry.y.values[0]], 
                    color='red', linestyle='--', linewidth=0.5)
    
    plt.legend()
    plt.title('Vessel Proximity Events')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.show()

# Visualize
visualize_proximity_events(data, proximity_data)