import math
import folium

# Constants
EARTH_RADIUS_FEET = 20925646.325  # Earth radius in feet
FEET_TO_METERS = 0.3048  # Conversion factor from feet to meters

def calculate_new_gps_position(lat, lon, heading, distance_feet):
    # Convert distance to meters
    distance_meters = distance_feet * FEET_TO_METERS
    
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

# Example usage
original_lat = 46.3345  # Example latitude
original_lon = -113.3021  # Example longitude
heading = 308  # Example heading in degrees
distance_feet = 30  # Distance in feet

left_position, right_position = calculate_new_gps_position(original_lat, original_lon, heading, distance_feet)

# Create a folium map centered at the original position
m = folium.Map(location=[original_lat, original_lon], zoom_start=20)

# Add markers for the original, left, and right positions
folium.Marker([original_lat, original_lon], popup='Original Position', icon=folium.Icon(color='blue')).add_to(m)
folium.Marker([left_position[0], left_position[1]], popup='Left Position', icon=folium.Icon(color='green')).add_to(m)
folium.Marker([right_position[0], right_position[1]], popup='Right Position', icon=folium.Icon(color='red')).add_to(m)

# Save the map to an HTML file and display it
m.save('./map.html')
m
