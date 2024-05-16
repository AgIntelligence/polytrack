import serial
import time
import csv
import re

# Replace 'COM_PORT' with the actual port your Bluetooth device is connected to.
# On a Mac, it might be something like '/dev/tty.YourBluetoothDevice-SerialPort'
SERIAL_PORT = '/dev/cu.AGAIGPS'  # Adjust this to your actual port
BAUD_RATE = 115200  # Make sure this matches the baud rate of your Bluetooth device

# Regular expression to parse the incoming data
pattern = re.compile(r"Lat: ([\d.-]+)\s*Long: ([\d.-]+)\s*Alt: ([\d.-]+) feet\s*Speed: ([\d.-]+) mph\s*Heading: ([\d.-]+) degrees")

# CSV file setup
csv_file = 'gps_data.csv'

# Initialize CSV file with headers if it doesn't exist
with open(csv_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Timestamp', 'Latitude', 'Longitude', 'Altitude (feet)', 'Speed (mph)', 'Heading (degrees)'])

# Function to parse and save data
def parse_and_save(data_block):
    match = pattern.match(data_block)
    if match:
        data = match.groups()
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        row = [timestamp] + list(data)
        print(f"Timestamp: {timestamp}, Latitude: {data[0]}, Longitude: {data[1]}, Altitude: {data[2]} feet, Speed: {data[3]} mph, Heading: {data[4]} degrees")
        with open(csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(row)

# Buffer to accumulate data
buffer = ""

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud rate.")
except serial.SerialException as e:
    print(f"Error: Could not open serial port {SERIAL_PORT}: {e}")
    exit()

try:
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()
            print(f"Raw data: {line}")
            if line.startswith("Lat:"):
                buffer = line
            elif buffer and not line.startswith("Lat:"):
                buffer += " " + line
                if "Heading" in line:
                    parse_and_save(buffer)
                    buffer = ""
except KeyboardInterrupt:
    print("Exiting script.")
finally:
    ser.close()
    print("Serial port closed.")
