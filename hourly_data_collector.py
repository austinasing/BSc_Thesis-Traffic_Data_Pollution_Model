# traffic data packages + others:
import numpy as np
import webdriver_manager.chrome
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
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
from datetime import datetime, timedelta
import schedule
import pytz

# all timestamps are for hour before the labelled time

# traffic scraper will append to the traffic city csv with a list of the rgb values of the ss and timestamp
def traffic_scraper():

    # center points of sites: Amsterdam, Rotterdam, Den Haag, Utrecht, Eindhoven
    study_sites = [['52.3693755,4.905404', 'Ams'], ['51.9181948,4.4495829', 'Rot'],
                   ['52.0666829,4.3148178', 'DnH'], ['52.0875317,5.1280634', 'Utc'],
                   ['51.440069,5.4655401', 'Edn']]

    for city in study_sites:
        # webdriver + maximize to get full data
        driver = webdriver.Chrome(ChromeDriverManager().install())

        #options = Options()
        #options.headless = True
        driver.maximize_window()

        # open up google traffic chrome webpage at empirically found zoom: 12.55
        traffic_url = fr'https://www.google.com/maps/@{city[0]},12.55z/data=!5m1!1e1'
        driver.get(traffic_url)

        # finds button and click to reject cookies
        accept = driver.find_element_by_xpath(
            '/html/body/c-wiz/div/div/div/div[2]/div[1]/div[3]/div[1]/div[1]/form[1]/div/div/button')
        accept.click()

        # wait one second to load the page but not load the overlay that obscures info
        # sleep(1.5)

        # take screenshot of webpage and quit
        img_filename = fr'C:\Users\austi\Downloads\model_data\traffic\ta_ss_{city[1]}.png'
        driver.get_screenshot_as_file(img_filename)
        driver.quit()

        # Collect the time of the screenshot taken from its metadata
        mtime = os.path.getmtime(img_filename)
        mtime_str = time.strftime('%Y%m%d%H%M%S', time.localtime(mtime))
        print(f'T_Timestamp: {mtime_str}')

        # Open image and convert to jpg
        traff_img_png = Image.open(img_filename)
        traff_img_jpg = traff_img_png.convert('RGB')

        # Convert image into list of RGB data per pixel
        pix_val = list(traff_img_jpg.getdata())
        pix_list = [list(ele) for ele in pix_val]

        print(f'T_length: {len(pix_list)}')

        # add a label to the first list item for the csv
        pix_list.insert(0, f'{city[1]}_{mtime_str}')

        # Save the list to a city csv with the first column being the city code + datetimestamp
        with open(fr'C:\Users\austi\Downloads\model_data\traffic\Img_Data\{city[1]}_traffic.csv', 'a',
                  newline='') as f:
            writer = csv.writer(f)
            writer.writerow(pix_list)
        f.close()
        print(f'T_Saved: {city[1]}_{mtime_str}')
        print("---")

def meteo_data():
    # datetime for meteorology extractor UTC (just for API, data is labelled in AMS)
    timestamp_now = datetime.utcnow()
    timestamp_one_hour_ago = timestamp_now - timedelta(hours=1) - timedelta(minutes=timestamp_now.minute % 10)
    filename = f"KMDS__OPER_P___10M_OBS_L2_{timestamp_one_hour_ago.strftime('%Y%m%d%H%M')}.nc"

    # meteorology request will append to the meteo city csv with a list of meteo variables and timestamp
    # KNMI API code more or less taken from their website
    def meteorology_request():
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

        # Append data from NetCDF4 to city meteo csv
        f = netCDF4.Dataset(filename)
        stations = [['Ams', 12], ['Rot', 42], ['DnH', 7], ['Utc', 20], ['Edn', 46], ['Mas', 50]]

        for i in range(len(stations)):
            name = str(f.variables['stationname'][stations[i][1]])
            avg_temp = float(f.variables['ta'][stations[i][1]])
            amb_temp = float(f.variables['tx'][stations[i][1]])
            solar_rad = float(f.variables['qg'][stations[i][1]])
            sun_dur = float(f.variables['ss'][stations[i][1]])
            wind_spd = float(f.variables['ff'][stations[i][1]])
            wind_gust = float(f.variables['gff'][stations[i][1]])
            wind_dir = float(f.variables['dd'][stations[i][1]])
            relative_hum = float(f.variables['rh'][stations[i][1]])
            pressure = float(f.variables['pp'][stations[i][1]])
            precip = float(f.variables['pg'][stations[i][1]])
            precip2 = float(f.variables['D1H'][stations[i][1]])

            # Convert timestamp label into CEST (Amsterdam)
            timestamp_CEST = timestamp_now + timedelta(hours=1)
            timestamp = timestamp_CEST.strftime('%Y%m%d%H%M')

            weather_list_reader = [name, timestamp, avg_temp, amb_temp, solar_rad, sun_dur, wind_spd, wind_gust, wind_dir,
                                   relative_hum, pressure, precip, precip2]
            print(weather_list_reader)

            # Save the list to a city csv raw for minute values
            with open(fr'C:\Users\austi\Downloads\model_data\meteo\{stations[i][0]}_meteo_raw.csv', 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(weather_list_reader)
            file.close()

            print(f'Appended: {stations[i][0]}')

        # Closes the netCDF4 file
        f.close()
    meteorology_request()
    # Delete the downloaded file
    os.remove(filename)

# Average the values for the raw meteorology data and append them to the new csv with correct hour timestamp


# NO2 request will append the NO2 value to the NO2 city csv (g/m3)
def NO2_request():

    # cities dictionary of all relevant station names and codes
    cities = {'Ams': [{'Kantershof' : 'NL49021'}, {'Nieuwendammerdijk': 'NL49003'}, {'Oude Schans': 'NL49019'}, {'Stadhouderskade': 'NL49017'}, {'Vondelpark': 'NL49014'}, {'Jan Van GalenStraat': 'NL49020'}, {'Van Diementstraat': 'NL49012'}, {'Haarlemmerweg': 'NL49002'}, {'Einsteinweg': 'NL49007'}, {'Ookmeer': 'NL49022'},
                      {'Zaanstad-Hemkade': 'NL49546'}, {'Badhoevedorp-Sloterweg': 'NL49561'}, {'Spaarnwoude-Machineweg': 'NL49703'}],
              'Rot': [{'Schiedamsevest': 'NL10418'}, {'Statenweg': 'NL01493'}, {'Zwartewaalstraat': 'NL01488'}, {'Pleinweg': 'NL01487'}, {'Hoogvliet': 'NL01485'},
                      {'Overschie-A13': 'NL01491'}, {'Schiedam-A.Arien': 'NL01494'}, {'Riddekerk-A16': 'NL01489'}, {'Riddekerk-Voorweg': 'NL01912'}, {'Vlaardingen-Riouwlaan': 'NL10449'}],
              'DnH': [{'Rebequestraat': 'NL10404'}, {'Amsterdamse Veerkade': 'NL10445'}, {'Neherkade': 'NL10450'}, {'Bleriotlaan': 'NL10446'}],
              'Utc': [{'Kardinaal de Jongweg': 'NL10636'}, {'Griftpark': 'NL10643'}, {'Constant Erzeijstraat': 'NL10639'}],
              'Edn': [{'Genovevalaan': 'NL10236'}, {'Noordbrbantlaan': 'NL10237'}, {'Veldhoven-Europlaan': 'NL10247'}],
              'Mas': [{''}]
              }

    # Iterates through the 5 cities
    for city in cities:
        # Iterates though the stations in each city
        for i in range(len(cities[city])):
            # Indexes the value (the station code) from the key (the station name)
            for key in cities[city][i]:

                # Requests the NO2 values from the city code
                params = {'formula': 'NO2'}
                response = requests.get(f'https://api.luchtmeetnet.nl/open_api/stations/{cities[city][i][key]}/measurements',params=params)
                response_dict = response.json()
                no2_data = response_dict['data']

                # Gets timestamp, converts to Amsterdam time and makes it readable
                time_value = (no2_data[0]['timestamp_measured'])
                UTC_timestamp = datetime.fromisoformat(time_value)
                unformat_CEST = UTC_timestamp + timedelta(hours=3)
                timestamp = unformat_CEST.strftime("%Y%m%d%H")

                # Write NO2 data to city csv with timestamp, station name, code, and data
                # No data = 'nan' in csv
                if len(no2_data) == 0:
                    row = [timestamp, key, cities[city][i][key], float('nan')]
                    with open(fr'C:\Users\austi\Downloads\model_data\NO2\{city}_NO2.csv', 'a',
                              newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow(row)

                        print(f"Appended 'nan' to {city}_NO2.csv")
                    file.close()
                else:
                    no2_value = (no2_data[0]['value'])
                    row = [timestamp, key, cities[city][i][key], no2_value]
                    with open(fr'C:\Users\austi\Downloads\model_data\NO2\{city}_NO2.csv', 'a',
                              newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow(row)

                        print(f"Appended {no2_value} to {city}_NO2.csv")
                    file.close()

# Stops the bot when the day is done
def exit_program():
    print('Complete for the day, good night')
    sys.exit(0)

# Schedule code to collect data 6am - 8pm every day. Traff + Meteo = 10 min, Meteo Average + NO2 = Hourly
for hour in range(6, 21):
    #for minute in range(0, 60, 10):
        #schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(meteo_data)
        # Traffic scraper takes longer ~5 min
        # schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(traffic_scraper)
        # will just do hourly for the first week when I can't check up on it
    try:
        schedule.every().day.at(f"{hour:02d}:00").do(meteo_data)
    except Exception as e:
        print(f"Error: {e}")
    #schedule.every().hour.at(":00").do(traffic_scraper)
    try:
        schedule.every().day.at(f"{hour:02d}:00").do(traffic_scraper)
    except Exception as e:
        print(f"Error: {e}")
    #schedule.every().hour.at(":00").do(NO2_request)
    try:
        schedule.every().day.at(f"{hour:02d}:00").do(NO2_request)
    except Exception as e:
        print(f"Error: {e}")

# Exits the program at the end of the day
schedule.every().day.at("22:00").do(exit_program)

while True:
    try:
        schedule.run_pending()
        now = datetime.now()
        time.sleep(600)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(600)