import csv
import math
import folium

# Constants
EARTH_RADIUS_FEET = 20925646.325  # Earth radius in feet
FEET_TO_METERS = 0.3048  # Conversion factor from feet to meters

def calculate_new_gps_position(lat, lon, heading, distance_feet):
    # Convert distance to meters
    distance_meters = (distance_feet / 2) * FEET_TO_METERS  # Use half the distance for each side
    
    # Convert latitude and longitude from degrees to radians
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    
    # Convert heading to radians
    heading_rad = math.radians(heading)
    
    # Calculate the left and right angles in radians
    left_angle_rad = heading_rad - math.pi / 2
    right_angle_rad = heading_rad + math.pi / 2
    
    # Calculate the new latitude and longitude for the left position
    left_lat_rad = math.asin(math.sin(lat_rad) * math.cos(distance_meters / EARTH_RADIUS_FEET) +
                             math.cos(lat_rad) * math.sin(distance_meters / EARTH_RADIUS_FEET) * math.cos(left_angle_rad))
    left_lon_rad = lon_rad + math.atan2(math.sin(left_angle_rad) * math.sin(distance_meters / EARTH_RADIUS_FEET) * math.cos(lat_rad),
                                        math.cos(distance_meters / EARTH_RADIUS_FEET) - math.sin(lat_rad) * math.sin(left_lat_rad))
    
    # Calculate the new latitude and longitude for the right position
    right_lat_rad = math.asin(math.sin(lat_rad) * math.cos(distance_meters / EARTH_RADIUS_FEET) +
                              math.cos(lat_rad) * math.sin(distance_meters / EARTH_RADIUS_FEET) * math.cos(right_angle_rad))
    right_lon_rad = lon_rad + math.atan2(math.sin(right_angle_rad) * math.sin(distance_meters / EARTH_RADIUS_FEET) * math.cos(lat_rad),
                                         math.cos(distance_meters / EARTH_RADIUS_FEET) - math.sin(lat_rad) * math.sin(right_lat_rad))
    
    # Convert the new latitude and longitude from radians to degrees
    left_lat = math.degrees(left_lat_rad)
    left_lon = math.degrees(left_lon_rad)
    right_lat = math.degrees(right_lat_rad)
    right_lon = math.degrees(right_lon_rad)
    
    return (left_lat, left_lon), (right_lat, right_lon)

# Initialize arrays to hold the left, center, and right positions
left_positions = []
center_positions = []
right_positions = []

# Read the CSV file
with open('gps_data.csv', 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        lat = float(row['Latitude'])
        lon = float(row['Longitude'])
        heading = float(row['Heading (degrees)'])
        distance_feet = 30  # Distance in feet
        
        left_position, right_position = calculate_new_gps_position(lat, lon, heading, distance_feet)
        
        # Append the positions to their respective arrays
        left_positions.append(left_position)
        center_positions.append((lat, lon))
        right_positions.append(right_position)

# Create an array that is the reverse of the right array
reverse_right_positions = list(reversed(right_positions))

# Add the first value of the left array to the end of the reversed right array
if left_positions:
    reverse_right_positions.append(left_positions[0])

# Create a new array that combines the left array with the reversed right array
combined_positions = left_positions + reverse_right_positions

# Create a folium map centered at the first position in the center positions array
if center_positions:
    m = folium.Map(location=[center_positions[0][0], center_positions[0][1]], zoom_start=20)
    
    # Add markers for each position
    for left_pos, center_pos, right_pos in zip(left_positions, center_positions, right_positions):
        folium.Marker([center_pos[0], center_pos[1]], popup='Center Position', icon=folium.Icon(color='blue')).add_to(m)
        folium.Marker([left_pos[0], left_pos[1]], popup='Left Position', icon=folium.Icon(color='green')).add_to(m)
        folium.Marker([right_pos[0], right_pos[1]], popup='Right Position', icon=folium.Icon(color='red')).add_to(m)
    
    # Add the polygon to the map
    folium.Polygon(locations=combined_positions, color='blue', fill=True, fill_opacity=0.5).add_to(m)
    
    # Save the map to an HTML file and display it
    m.save('./map.html')

print("Left positions:", left_positions)
print("Center positions:", center_positions)
print("Right positions:", right_positions)
print("Reversed right positions:", reverse_right_positions)
print("Combined positions:", combined_positions)
