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

def parse_and_process_gps_data(data_block):
    match = pattern.match(data_block)
    if match:
        data = match.groups()
        lat = float(data[0])
        lon = float(data[1])
        heading = float(data[4])
        distance_feet = 30  # Distance in feet
        
        left_position, right_position = calculate_new_gps_position(lat, lon, heading, distance_feet)
        
        # Create an array that is the reverse of the right array
        right_positions = [right_position]
        reverse_right_positions = list(reversed(right_positions))
        
        # Add the first value of the left array to the end of the reversed right array
        left_positions = [left_position]
        if left_positions:
            reverse_right_positions.append(left_positions[0])
        
        # Create a new array that combines the left array with the reversed right array
        combined_positions = left_positions + reverse_right_positions
        
        # Send the current location and, if tracking is on, the positions to the client
        socketio.emit('update_current_location', {
            'current_location': (lat, lon)
        })
        
        if tracking:
            socketio.emit('update_positions', {
                'left': left_positions,
                'center': [(lat, lon)],
                'right': right_positions,
                'combined': combined_positions
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
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # Start the Bluetooth reading thread
    bluetooth_thread = Thread(target=read_from_bluetooth)
    bluetooth_thread.daemon = True
    bluetooth_thread.start()
    
    # Start the Flask app
    socketio.run(app, host='0.0.0.0', port=5050)
