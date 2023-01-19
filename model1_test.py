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
import time

driver = webdriver.Chrome(ChromeDriverManager().install())
traffic_url = 'https://www.google.com/maps/@52.3727025,4.9246355,15z/data=!5m2!1e1!1e4'
driver.get(traffic_url)
driver.get_screenshot_as_file(r'C:\Users\Austin\PycharmProjects\capstone\Web_Screenshots\traffic_sstest.png')
driver.quit()