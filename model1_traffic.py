# traffic data packages + others:
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

###################################
# Google Maps Traffic Data Import #
###################################

# screenshot extraction
driver = webdriver.Chrome(ChromeDriverManager().install())
traffic_url = 'https://www.google.com/maps/@52.3727025,4.9246355,11z/data=!5m2!1e1!1e4'
driver.get(traffic_url)
driver.get_screenshot_as_file(r'C:\Users\Austin\PycharmProjects\capstone\Web_Screenshots\traffic_ss.png')
driver.quit()

# Open image and get image size for array building
traff_img_png = Image.open(r'C:\Users\Austin\PycharmProjects\capstone\Web_Screenshots\traffic_ss.png')
traff_img_jpg = traff_img_png.convert('RGB')
image_height = traff_img_jpg.size[1]
image_width = traff_img_jpg.size[0]

# Convert image into list of pixel data with RGB
pix_val = list(traff_img_jpg.getdata())
pix_val_list = [list(ele) for ele in pix_val]

# searches all pixels and converts colors to numbers
t_pixel_list = []
for color in pix_val_list:
    # converts list into integers
    def convert(list):
        s = [str(i) for i in list]
        res = int("".join(s))
        return(res)

    if 99214104 <= convert(color) <= 107216112:
        color = 1
    elif 25515177 <= convert(color) <= 25515482:
        color = 2
    elif 2426050 <= convert(color) <= 2437060:
        color = 3
    elif 1293131 <= convert(color) <= 1394949:
        color = 4
    else:
        color = 0
    t_pixel_list.append(int(color))

# create single traffic severity value (could combine this with color classifier to make code smaller)
green = []
yellow = []
orange = []
red = []
for values in t_pixel_list:
    if values == 1:
        green.append(int(values))
    if values == 2:
        yellow.append(int(values))
    if values == 3:
        orange.append(int(values))
    if values == 4:
        red.append(int(values))

# need to define weights by scientific values
yellow_weight = 1
orange_weight = 2
red_weight = 3
total_traffic = len(green) + len(yellow) + len(orange) + len(red)
traffic_severity =((len(yellow) / total_traffic) * yellow_weight) + ((len(orange) / total_traffic) * orange_weight) + ((len(red) / total_traffic) * red_weight)
print(f'Traffic Severity Level: {traffic_severity * 100}')

