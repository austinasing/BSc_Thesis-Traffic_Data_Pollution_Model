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
import time

import csv
from datetime import datetime

print('Press Ctrl-C or stop program to stop collecting data and start MLR')

weather_counter = 0
hourly_counter = 0
try:
    while (True):
        now = datetime.now()

        def traffic_extractor():
            # screenshot extraction
            driver = webdriver.Chrome(ChromeDriverManager().install())
            traffic_url = 'https://www.google.com/maps/@52.3727025,4.9246355,11z/data=!5m2!1e1!1e4'
            driver.get(traffic_url)
            driver.get_screenshot_as_file(r'C:\Users\Austin\PycharmProjects\capstone\Web_Screenshots\traffic_ss.png')
            driver.quit()

            # Open image and get image size for array building
            traff_img_png = Image.open(r'C:\Users\Austin\PycharmProjects\capstone\Web_Screenshots\traffic_ss.png')
            traff_img_jpg = traff_img_png.convert('RGB')

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
            return (traffic_severity)
        traff_value = traffic_extractor()

        row = {'DateTime': now.strftime('%Y%m%d%H%M'), 'Traffic Severity': traff_value, 'Temperature': '',
               'Solar Radiance': '', 'Wind Speed': '', 'Relative Humidity': '', 'Pressure': ''}
        # appends new row of csv with row list ^
        with open('model1_data_raw.csv', 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            writer.writerow(row)
        f.close()
        print(f'Appended Datetime: {now}')
        print(f'Appended Traffic Severity: {traff_value}')

        # datetime for meteorology extractor
        timestamp_now = datetime.utcnow()
        timestamp_one_hour_ago = timestamp_now - timedelta(hours=1) - timedelta(minutes=timestamp_now.minute % 10)
        filename = f"KMDS__OPER_P___10M_OBS_L2_{timestamp_one_hour_ago.strftime('%Y%m%d%H%M')}.nc"

        # delay mechanism so that weather data and traffic data line-up
        if weather_counter < 12:
            weather_counter += 1
        hourly_counter += 1
        print(f'Hourly Counter= {hourly_counter}')
        print(f'Weather Counter= {weather_counter} \n')

        if weather_counter >= 6:
            print('Running Meteorology Extractor...')
            def meteorology_extractor():
                # code from KNMI to extract file from 1 hour ago
                logging.basicConfig()
                logger = logging.getLogger(__name__)
                logger.setLevel(os.environ.get("LOG_LEVEL", logging.INFO))

                api_url = "https://api.dataplatform.knmi.nl/open-data"
                api_version = "v1"

                def main():
                    api_key = "eyJvcmciOiI1ZTU1NGUxOTI3NGE5NjAwMDEyYTNlYjEiLCJpZCI6IjY4MjFhYWZiODIyYzRjYjc5MzA2OTc1ZTljYTU1ZGE5IiwiaCI6Im11cm11cjEyOCJ9"
                    dataset_name = "Actuele10mindataKNMIstations"
                    dataset_version = "2"

                    logger.debug(f"Current time: {timestamp_now}")
                    logger.debug(f"One hour ago:{timestamp_one_hour_ago}")
                    logger.debug(f"Dataset file to download: {filename}")

                    endpoint = f"{api_url}/{api_version}/datasets/{dataset_name}/versions/{dataset_version}/files/{filename}/url"
                    get_file_response = requests.get(endpoint, headers={"Authorization": api_key})

                    if get_file_response.status_code != 200:
                        logger.error("Unable to retrieve download url for file")
                        logger.error(get_file_response.text)
                        sys.exit(1)

                    logger.info(f"Successfully retrieved temporary download URL for dataset file {filename}")

                    download_url = get_file_response.json().get("temporaryDownloadUrl")

                    if "X-KNMI-Deprecation" in get_file_response.headers:
                        deprecation_message = get_file_response.headers.get("X-KNMI-Deprecation")
                        logger.warning(f"Deprecation message: {deprecation_message}")

                    download_file_from_temporary_download_url(download_url, filename)

                def download_file_from_temporary_download_url(download_url, filename):
                    try:
                        with requests.get(download_url, stream=True) as r:
                            r.raise_for_status()
                            with open(filename, "wb") as f:
                                for chunk in r.iter_content(chunk_size=8192):
                                    f.write(chunk)
                    except Exception:
                        logger.exception("Unable to download file using download URL")
                        sys.exit(1)

                    logger.info(f"Successfully downloaded dataset file to {filename}")

                if __name__ == "__main__":
                    main()

                # sleep(5) shouldn't be necessary but in case it breaks

                # reads downloaded netcdf file and extracts wanted variables for schipol station and puts them in a list
                def knmi_file_reader():
                    f = netCDF4.Dataset(filename)

                    # min_temp = float(f.variables['tn'][14])
                    # max_temp = float(f.variables['tx'][14])
                    avg_temp = float(f.variables['ta'][14])
                    solar_rad = float(f.variables['qg'][14])
                    wind_spd = float(f.variables['ff'][14])
                    relative_hum = float(f.variables['rh'][14])
                    pressure = float(f.variables['pp'][14])
                    time_sec = float(f.variables['time'][:])
                    time_norm = int(datetime.fromtimestamp(time_sec).strftime('%Y%m%d%H%M')) - 2000000000

                    weather_list_reader = [avg_temp, solar_rad, wind_spd, relative_hum, pressure, time_norm]
                    return (weather_list_reader)

                weather_list = knmi_file_reader()
                return (weather_list)
            meteo_data = meteorology_extractor()
            print(f'Appending Meteorology Data: {meteo_data} to raw data file')

            # adds meteorology into empty columns of csv for correct time
            df = pd.read_csv('model1_data_raw.csv')

            df.loc[df.index[-6], 'Temperature'] = meteo_data[0]
            df.loc[df.index[-6], 'Solar Radiance'] = meteo_data[1]
            df.loc[df.index[-6], 'Wind Speed'] = meteo_data[2]
            df.loc[df.index[-6], 'Relative Humidity'] = meteo_data[3]
            df.loc[df.index[-6], 'Pressure'] = meteo_data[4]
            df.loc[df.index[-6], 'WeatherTime'] = meteo_data[5]

            df.to_csv('model1_data_raw.csv', index=False)

            # had issue with remove file bc it was being used in second iteration
            # os.remove(filename)

        # delay so that all data is available for analysis to run
        if weather_counter >= 12:
            if hourly_counter == 6:
                print('Running Air Quality Extractor...')
                def air_quality_extractor():
                    # collects station numbers for Amsterdam Stations to get only data from these stations
                    station_numbers = []
                    for page in range(1, 5):
                        params = {'page': page}
                        response = requests.get('https://api.luchtmeetnet.nl/open_api/stations', params=params)
                        response_dict = response.json()

                        data = response_dict['data']
                        for entry in data:
                            if 'Amsterdam' in entry['location']:
                                station_numbers.append(entry['number'])
                    # can add elif here for more stations

                    # collects NO2 values for each station and the timestamp
                    timestamps = []
                    no2_values = []
                    for number in station_numbers:
                        params = {'formula': 'NO2'}
                        response = requests.get(f'https://api.luchtmeetnet.nl/open_api/stations/{number}/measurements',
                                                params=params)
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
                    return [no2_average, hourly_timestamp]
                air_quality_list = air_quality_extractor()
                avg_no2 = air_quality_list[0]
                hourly_timestamp = air_quality_list[1]

                # average raw data values of last 6 rows
                def hourly_averager():
                    df = pd.read_csv('model1_data_raw.csv')

                    traff_severity = df.iloc[[-1, -2, -3, -4, -5, -6], [1]]
                    t_sev_list = traff_severity['Traffic Severity'].values.tolist()
                    t_sev_avg = sum(t_sev_list) / len(t_sev_list)

                    temp = df.iloc[[-1, -2, -3, -4, -5, -6], [2]]
                    temp_list = temp['Temperature'].values.tolist()
                    temp_avg = sum(temp_list) / len(temp_list)

                    solar_rad = df.iloc[[-1, -2, -3, -4, -5, -6], [3]]
                    sr_list = solar_rad['Solar Radiance'].values.tolist()
                    sr_avg = sum(sr_list) / len(sr_list)

                    wind_spd = df.iloc[[-1, -2, -3, -4, -5, -6], [4]]
                    ws_list = wind_spd['Wind Speed'].values.tolist()
                    ws_avg = sum(ws_list) / len(ws_list)

                    relative_hum = df.iloc[[-1, -2, -3, -4, -5, -6], [5]]
                    rh_list = relative_hum['Relative Humidity'].values.tolist()
                    rh_avg = sum(rh_list) / len(rh_list)

                    pressure = df.iloc[[-1, -2, -3, -4, -5, -6], [6]]
                    p_list = pressure['Pressure'].values.tolist()
                    p_avg = sum(p_list) / len(p_list)
                    return[t_sev_avg, temp_avg, sr_avg, ws_avg, rh_avg, p_avg]
                hourly_list = hourly_averager()

                # classify time as an independant variable (right now loosely based on PBL but idk if more or less classes would be beneficial)
                time_int = (hourly_timestamp[11:13])
                if 6 <= int(time_int) <= 10:
                    time_value = 3
                elif 10 < int(time_int) <= 16:
                    time_value = 6
                elif 16 < int(time_int) <= 20:
                    time_value = 10

                # append values to model1_data_hourly_csv
                hour_row = {'DateTime': hourly_timestamp, 'Time_IV': time_value, 'Traffic Severity': hourly_list[0], 'Temperature': hourly_list[1],
                       'Solar Radiance': hourly_list[2], 'Wind Speed': hourly_list[3], 'Relative Humidity': hourly_list[4], 'Pressure': hourly_list[5], 'NO2': avg_no2}
                # appends new row of csv with row list ^
                with open('model1_data_hourly.csv', 'a', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=hour_row.keys())
                    writer.writerow(hour_row)
                f.close()

                hourly_counter = 0
        if hourly_counter == 6:
            hourly_counter = 0

        # 10 minutes inbetween row uploading of raw_data
        # traffic extraction takes 12 extra secs
        # meteo extraction takes ...
        # to be completely synchronous, will want to take both of these into account
        time.sleep(3600-12)
except KeyboardInterrupt:
    pass

print('Running MLR')
'''
#standardize independant variables from 0-10
mlr = pd.read_csv('model1_data_hourly.csv')
# could prob do this in a for loop
mlr['Traffic Severity'] = (mlr['Traffic Severity'] / mlr['Traffic Severity'].max()) * 10
mlr['Temperature'] = (mlr['Temperature'] / mlr['Temperature'].max()) * 10
mlr['Solar Radiance'] = (mlr['Solar Radiance'] / mlr['Solar Radiance'].max()) * 10
mlr['Wind Speed'] = (mlr['Wind Speed'] / mlr['Wind Speed'].max()) * 10
mlr['Relative Humidity'] = (mlr['Relative Humidity'] / mlr['Relative Humidity'].max()) * 10
mlr['Pressure'] = (mlr['Pressure'] / mlr['Pressure'].max()) * 10

# calculate MLR'''