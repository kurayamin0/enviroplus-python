#!/usr/bin/env python3

""" Script by Kurayamin0 https://github.com/kurayamin0/enviroplus-python """

import colorsys
import sys
import time
from datetime import datetime
import csv

import st7735

try:
    # Transitional fix for breaking change in LTR559
    from ltr559 import LTR559
    ltr559 = LTR559()
except ImportError:
    import ltr559

from subprocess import PIPE, Popen

from bme280 import BME280
from fonts.ttf import RobotoMedium as UserFont
from PIL import Image, ImageDraw, ImageFont
from pms5003 import PMS5003
from pms5003 import ReadTimeoutError as pmsReadTimeoutError
from pms5003 import SerialTimeoutError

from enviroplus import gas

# BME280 temperature/pressure/humidity sensor
bme280 = BME280()

# PMS5003 particulate sensor
pms5003 = PMS5003()

# Create an empty list to store data
data_buffer = []

# Create ST7735 LCD display class
st7735 = st7735.ST7735(
    port=0,
    cs=1,
    dc="GPIO9",
    backlight="GPIO12",
    rotation=270,
    spi_speed_hz=10000000
)

# Initialize display
st7735.begin()

WIDTH = st7735.width
HEIGHT = st7735.height
font = ImageFont.truetype(UserFont, 20)

# Get the temperature of the CPU for compensation
def get_cpu_temperature():
    with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
        temp = f.read()
        temp = int(temp) /1000.0
    return temp

# Tuning factor for compensation
factor = 2.25
cpu_temps = [get_cpu_temperature()] * 5 # Initalize with CPU temp

# Function to get sensor readings
def get_readings():
    readings = {}
    readings['timestamp'] = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    # Enviromental readings
    raw_temp = bme280.get_temperature()
    cpu_temp = get_cpu_temperature()

    # Smooth out CPU temperature with averaging to reduce jitter
    cpu_temps.append(cpu_temp)
    cpu_temps.pop(0)
    avg_cpu_temp = sum(cpu_temps) / len(cpu_temps)

    # Environmental readings
    compensated_temp = raw_temp - ((avg_cpu_temp - raw_temp) / factor)
    readings['temperature'] = compensated_temp
    readings['humidity'] = bme280.get_humidity()
    readings['pressure'] = bme280.get_pressure()

    # Light readings
    readings['light'] = ltr559.get_lux()

    # Gas readings (oxidising, reducing, NH3)
    gas_data = gas.read_all()
    readings['oxidising'] = gas_data.oxidising / 1000  # Convert to kOhms
    readings['reducing'] = gas_data.reducing / 1000  # Convert to kOhms
    readings['nh3'] = gas_data.nh3 / 1000  # Convert to kOhms

    # PMS5003 readings (try-except for handling timeouts)
    try:
        pm_data = pms5003.read()
        readings['pm1'] = pm_data.pm_ug_per_m3(1.0)
        readings['pm2_5'] = pm_data.pm_ug_per_m3(2.5)
        readings['pm10'] = pm_data.pm_ug_per_m3(10)
    except pmsReadTimeoutError:
        readings['pm1'], readings['pm2_5'], readings['pm10'] = None, None, None

    return readings

# Function to display data on LCD
def display_readings(readings):
    # Create a blank image for drawing
    image = Image.new('RGB', (WIDTH, HEIGHT), color=(0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Display the sensor data
    draw.text((0, 0), f"Temp: {readings['temperature']:.2f}C", font=font, fill=(255, 255, 255))
    draw.text((0, 25), f"Hum: {readings['humidity']:.2f}%", font=font, fill=(255, 255, 255))
    draw.text((0, 50), f"Press: {readings['pressure']:.2f}hPa", font=font, fill=(255, 255, 255))
    draw.text((0, 75), f"Light: {readings['light']} lux", font=font, fill=(255, 255, 255))
    draw.text((0, 100), f"Ox: {readings['oxidising']:.2f}kOhms", font=font, fill=(255, 255, 255))
    draw.text((0, 125), f"Red: {readings['reducing']:.2f}kOhms", font=font, fill=(255, 255, 255))
    draw.text((0, 150), f"NH3: {readings['nh3']:.2f}kOhms", font=font, fill=(255, 255, 255))
    
    # Adjust Y positions for PM readings to avoid overlap
    draw.text((0, 175), f"PM1.0: {readings['pm1']} ug/m3", font=font, fill=(255, 255, 255))
    draw.text((0, 200), f"PM2.5: {readings['pm2_5']} ug/m3", font=font, fill=(255, 255, 255))
    draw.text((0, 225), f"PM10: {readings['pm10']} ug/m3", font=font, fill=(255, 255, 255))

    # Update display with the image
    st7735.display(image)

# Function to save data to a CSV file
def save_to_csv(data):
    filename = "sensor_data.csv"
    file_exists = False

    # Check if file exists to write headers
    try:
        with open(filename, 'r'):
            file_exists = True
    except FileNotFoundError:
        pass

    # Write data to CSV
    with open(filename, 'a', newline='') as csvfile:
        fieldnames = ['timestamp', 'temperature', 'humidity', 'pressure', 'light', 'oxidising', 'reducing', 'nh3', 'pm1', 'pm2_5', 'pm10']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Write headers only if file is new
        if not file_exists:
            writer.writeheader()

        for row in data:
            writer.writerow(row)

# Main loop to collect and write data
if __name__ == "__main__":
    start_time = time.time()

    while True:
        # Collect readings every 5 seconds
        readings = get_readings()
        data_buffer.append(readings)
        
        # Display readings on the LCD
        display_readings(readings)
        
        time.sleep(5)  # 5 seconds

        # Save data to CSV every 15 minutes
        if time.time() - start_time >= 900:  # 900 seconds = 15 minutes
            save_to_csv(data_buffer)
            data_buffer = []  # Clear
            start_time = time.time()  # Reset start time
