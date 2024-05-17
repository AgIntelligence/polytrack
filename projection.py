import csv
import math
import serial
import time
import re
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from threading import Thread

# Constants
EARTH_RADIUS_FEET = 20925646.325  # Earth radius in feet
FEET_TO_METERS = 0.3048  # Conversion factor from feet to meters

# Serial port configuration
SERIAL_PORT = '/dev/cu.AGAIGPS'  # Adjust this to your actual port
BAUD_RATE = 115200  # Make sure this matches the baud rate of your Bluetooth device

# Regular expression to parse the incoming data
pattern = re.compile(r"Lat: ([\d.-]+)\s*Long: ([\d.-]+)\s*Alt: ([\d.-]+) feet\s*Speed: ([\d.-]+) mph\s*Heading: ([\d.-]+) degrees")

# Flask app setup
app = Flask(__name__)
socketio = SocketIO(app)

# Flag to control tracking state
tracking = False

# List to store the user's path
user_path = []
left_path = []
right_path = []

# Function to calculate the new GPS positions for the front and rear projections
def calculate_new_gps_positions(lat, lon, heading, distance_feet):
    # Convert distance to meters
    distance_meters = (distance_feet / 2) * FEET_TO_METERS
    
    # Convert latitude and longitude from degrees to radians
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    
    # Convert heading to radians
    heading_rad = math.radians(heading)
    
    # Calculate angles for left and right projections
    left_angle_rad = heading_rad - math.pi / 2
    right_angle_rad = heading_rad + math.pi / 2
    front_angle_rad = heading_rad  # Same direction as heading
    
    # Calculate front left and right positions
    front_left_lat, front_left_lon = calculate_position(lat_rad, lon_rad, distance_meters, left_angle_rad, front_angle_rad)
    front_right_lat, front_right_lon = calculate_position(lat_rad, lon_rad, distance_meters, right_angle_rad, front_angle_rad)
    
    # Calculate rear left and right positions
    rear_left_lat, rear_left_lon = calculate_position(lat_rad, lon_rad, distance_meters, left_angle_rad, heading_rad + math.pi)
    rear_right_lat, rear_right_lon = calculate_position(lat_rad, lon_rad, distance_meters, right_angle_rad, heading_rad + math.pi)
    
    # Calculate the front projection point
    front_projection_lat, front_projection_lon = calculate_position(lat_rad, lon_rad, distance_feet, heading_rad, heading_rad)
    
    return (front_left_lat, front_left_lon), (front_right_lat, front_right_lon), (rear_left_lat, rear_left_lon), (rear_right_lat, rear_right_lon), (front_projection_lat, front_projection_lon)

# Helper function to calculate new latitude and longitude based on distance and angle
def calculate_position(lat_rad, lon_rad, distance_meters, side_angle_rad, direction_angle_rad):
    new_lat_rad = math.asin(math.sin(lat_rad) * math.cos(distance_meters / EARTH_RADIUS_FEET) +
                            math.cos(lat_rad) * math.sin(distance_meters / EARTH_RADIUS_FEET) * math.cos(side_angle_rad))
    new_lon_rad = lon_rad + math.atan2(math.sin(side_angle_rad) * math.sin(distance_meters / EARTH_RADIUS_FEET) * math.cos(lat_rad),
                                       math.cos(distance_meters / EARTH_RADIUS_FEET) - math.sin(lat_rad) * math.sin(new_lat_rad))
    return math.degrees(new_lat_rad), math.degrees(new_lon_rad)

def parse_and_process_gps_data(data_block):
    match = pattern.match(data_block)
    if match:
        data = match.groups()
        lat = float(data[0])
        lon = float(data[1])
        heading = float(data[4])
        distance_feet = 30  # Distance in feet
        
        front_left, front_right, rear_left, rear_right, front_projection = calculate_new_gps_positions(lat, lon, heading, distance_feet)
        
        # Create arrays for front and rear positions
        front_positions = [front_left, front_right]
        rear_positions = [rear_left, rear_right]
        
        # Add current position to user_path
        if tracking:
            user_path.append((lat, lon))
            left_path.append(rear_left)
            right_path.append(rear_right)
        
        # Create a new array that combines the left path and the reversed right path
        combined_positions = left_path + list(reversed(right_path))
        
        # Send the current location and the positions to the client
        socketio.emit('update_current_location', {
            'current_location': (lat, lon)
        })
        
        if tracking:
            socketio.emit('update_positions', {
                'front': front_positions,
                'combined': combined_positions,
                'front_projection': front_projection
            })

def read_from_bluetooth():
    global tracking
    buffer = ""
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud rate.")
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                print(f"Raw data: {line}")
                if line.startswith("Lat:"):
                    buffer = line
                elif buffer and not line.startswith("Lat:"):
                    buffer += " " + line
                    if "Heading" in line:
                        parse_and_process_gps_data(buffer)
                        buffer = ""
    except serial.SerialException as e:
        print(f"Error: Could not open serial port {SERIAL_PORT}: {e}")
    finally:
        ser.close()
        print("Serial port closed.")

@socketio.on('toggle_tracking')
def handle_toggle_tracking():
    global tracking
    tracking = not tracking
    emit('tracking_status', {'tracking': tracking})

@app.route('/')
def project():
    return render_template('project.html')

if __name__ == '__main__':
    # Start the Bluetooth reading thread
    bluetooth_thread = Thread(target=read_from_bluetooth)
    bluetooth_thread.daemon = True
    bluetooth_thread.start()
    
    # Start the Flask app
    socketio.run(app, host='0.0.0.0', port=5050)
