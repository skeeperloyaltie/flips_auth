# Kenya Area Visualization using Matplotlib

# Import necessary libraries
import matplotlib.pyplot as plt
import numpy as np

# Define the coordinates for Kenya
kenya_area_coordinates = [
    (34.816, 5.000),   # NW point
    (41.000, 5.000),   # NE point
    (41.000, -4.000),  # SE point
    (34.816, -4.000),  # SW point
    (34.816, 5.000)    # Closing the polygon
]

# Unzip the coordinates into two lists
lon, lat = zip(*kenya_area_coordinates)

# Create a plot
plt.figure(figsize=(10, 8))
plt.fill(lon, lat, color='lightblue', alpha=0.5)
plt.plot(lon, lat, marker='o', color='blue', markersize=5)

# Adding titles and labels
plt.title('Geographical Area of Kenya')
plt.xlabel('Longitude')
plt.ylabel('Latitude')

# Show grid
plt.grid()

# Show the plot
plt.show()
