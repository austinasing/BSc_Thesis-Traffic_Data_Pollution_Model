import numpy as np
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
from PIL import Image, ImageChops
from osgeo import gdal, osr, ogr
import os
import matplotlib.pyplot as plt

# weather data packages:
import logging
import os
import sys
from datetime import datetime
from datetime import timedelta
import requests
import netCDF4
import netCDF4 as nc
import matplotlib

# air quality data packages:
import pandas as pd
import datetime
import time

import csv
from datetime import datetime

# collects station numbers for Amsterdam Stations to get only data from these stations
station_numbers = []
for page in range(1, 5):
    params = {'page': page}
    response = requests.get('https://api.luchtmeetnet.nl/open_api/stations', params=params)
    response_dict = response.json()

    data = response_dict['data']
    for entry in data:
        if 'Amsterdam' in entry ['location']:
            station_numbers.append(entry['number'])
# can add elif here for more stations

# collects NO2 values for each station and the timestamp
timestamps = []
no2_values = []
for number in station_numbers:
    params = {'formula': 'NO2'}
    response = requests.get(f'https://api.luchtmeetnet.nl/open_api/stations/{number}/measurements',params=params)
    response_dict = response.json()

    no2_data = response_dict['data']
    if len(no2_data) == 0:
        no2_values.append(float('nan'))
    else:
        no2_values.append(no2_data[0]['value'])

    for entry in no2_data:
        timestamps.append(entry['timestamp_measured'])

# removes one station without NO2 values and computes average
del no2_values[5]
no2_average = sum(no2_values) / len(no2_values)
hourly_timestamp = timestamps[0]

print(no2_average)
print(hourly_timestamp)

time_int = (hourly_timestamp[11:13])
print(time_int)

# Method to extract value with their timestamp attached closest you can get is 19 days)
'''
url = 'https://api.luchtmeetnet.nl/open_api/measurements?station_number=&formula=NO2&page=1&order_by=timestamp_measured&order_direction=desc&end=2022-11-11T09:00:00&start=2022-11-11T09:00:00'
payload={}
headers = {}

response = requests.request("GET", url, headers=headers, data=payload)
response_dict = response.json()

dataframe3 = pd.DataFrame

stat_num = []
value = []
time = []
data = response_dict['data']
print(data[0])

n = 0
while n < 10:
    stat_num.append(data[n]['station_number'])
    value.append(data[n]['value'])
    time.append(data[n]['timestamp_measured'])
    n + 1

dataframe3['Station number'] = stat_num
dataframe3['NO2 Value'] = value
dataframe3['Datetime'] = time

print(dataframe3)'''''