import numpy as np
import csv
import matplotlib.pyplot as plt
import pandas as pd
import gdal
#['Mas', ['Heerlen-Jamboreepad', 'Heerlen-Looierstraat', 'Wijnandsrade-Opfergeltstraat']

cities = [['Ams', ['Zaanstad - Hemkade','Van Diemenstraat','Niewendammerdijk','Haarlemmerweg',
             'Einsteinweg','Jan Van Galenstraat','Oude Schans','Ookmeer','Vondelpark',
           'Stadhoudersake','Badhoevedorp - Sloterweg','Kantershof']],
          ['Rot', ['Schiedamsevest', 'Statenweg', 'Zwartewaalstraat', 'Pleinweg', 'Hoogvliet',
                   'Overschie-A13', 'Schiedam-A.Arien', 'Riddekerk-A16', 'Riddekerk-Voorweg', 'Vlaardingen-Riouwlaan']],
          ['DnH', ['Rebequestraat', 'Amsterdamse Veerkade', 'Neherkade', 'Bleriotlaan']],
          ['Utc', ['Kardinaal de Jongweg', 'Griftpark', 'Constant Erzeijstraat']],
          ['Edn', ['Genovevalaan', 'Noordbrbantlaan', 'Veldhoven-Europlaan']]]

      #    ['Rot', ['Schiedamsevest', 'Statenweg', 'Zwartewaalstraat','Pleinweg', 'Hoogvliet',
       #            'Overschie-A13','Schiedam-A.Arien', 'Riddekerk-A16', 'Riddekerk-Voorweg', 'Vlaardingen-Riouwlaan']],


for city in cities:

    # only calculates for training sets that I have data for
    t_timestamp = fr'C:\Users\Austin\Downloads\Capstone\Model Data\M4\{city[0]}_Timestamp_Dir.csv'
    df3 = pd.read_csv(t_timestamp, header=None)
    yesno = df3.iloc[0:, 1]
    wind_dir = df3.iloc[0:, 2]

    # load in roadtype tif as array
    tif_file = fr'C:\Users\Austin\Downloads\Capstone\Maps\{city[0]}_road_ras.tif'
    dataset = gdal.Open(tif_file)
    # Get the dimensions of the GeoTIFF
    rows = dataset.RasterYSize
    cols = dataset.RasterXSize
    # Create an empty list to hold the 2D array of data
    road_tif = []
    # Loop through each row of the GeoTIFF
    for i in range(rows):
        row = []
        for j in range(cols):
            # Read the pixel value at the current row and column
            band = dataset.GetRasterBand(1)
            value = band.ReadAsArray(j, i, 1, 1)[0][0]
            # Add the pixel value to the current row
            row.append(value)
        # Add the row to the 2D array of data
        road_tif.append(row)
    road_array = np.array(road_tif)

    # get station names and coordinates
    coord_file = fr'C:\Users\Austin\Downloads\Capstone\Maps\{city[0]}_coord2.csv'
    coord_list = []
    #names = ['Zaanstad - Hemkade','Van Diemenstraat','Niewendammerdijk','Haarlemmerweg',
     #        'Einsteinweg','Jan Van Galenstraat','Oude Schans','Ookmeer','Vondelpark',
      #       'Stadhoudersake','Badhoevedorp - Sloterweg','Kantershof']
    #match_strings = ['Schiedamsevest', 'Statenweg', 'Zwartewaalstraat','Pleinweg', 'Hoogvliet', 'Overschie-A13','Schiedam-A.Arien', 'Riddekerk-A16', 'Riddekerk-Voorweg', 'Vlaardingen-Riouwlaan']
    #match_strings = ['Amsterdamse Veerkade', 'Neherkade', 'Bleriotlaan']
    #match_strings = ['Kardinaal de Jongweg', 'Griftpark', 'Constant Erzeijstraat']
    #match_strings = ['Genovevalaan', 'Noordbrbantlaan', 'Veldhoven-Europlaan']
    names = city[1]

    with open(coord_file, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            for i in range(len(row)):
                row[i] = int(row[i])
            coord_list.append(row)

    # empty final dataframe
    new_df = pd.DataFrame(columns=names)
    road_df = pd.DataFrame(columns=names)
    # radius
    radius = 63
    # angle of the sector in which data is gathered
    sector_angle_rad = 3* (np.pi/4)

    # distance calculator for circle radius determining
    def calculate_distance(coord1, coord2):
        # Calculate the Euclidean distance between two coordinates
        x1, y1 = coord1
        x2, y2 = coord2
        return np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    # iterates over all ss saved in traffic file
    traffic_file = fr'C:\Users\Austin\Downloads\Capstone\Model Data\T4\{city[0]}_processf.csv'
    #split up traffic image file into chunks bc it doesn't have enough memeory to read the whole thing
    #also have to enumerate to keep track of how many chunks w i
    chunksize = 1
    for i,chunk in enumerate(pd.read_csv(traffic_file, header=None, chunksize=chunksize, low_memory=False)):
        print(f'Chunk loaded, Training set: {city[0]}, {i}')

        # if that training set has data (has been labelled as 1 in the t_timestamp.csv), then use
        if yesno[i] == 1:
            flat_array = np.array(chunk.iloc[0])
            matrix = flat_array.reshape((654, 948))

            # empty list to collect all the average values for each station
            station_values = []
            road_values = []
            # iterates over every coordinate in the list to do the calculation
            for coord in coord_list:
                row, col = coord

                # collect traffic value
                values = []
                #define the extent of the circle
                for o in range(matrix.shape[0]):
                    for j in range(matrix.shape[1]):
                        distance = calculate_distance((row, col), (o, j))
                        if distance <= radius and matrix[o, j] != 0:
                            #defines the sector and only counts values within the sector
                            deg = np.degrees(wind_dir[i])
                            angle = np.arctan2(j - col, o - row)
                            compass_angle = np.degrees(angle)
                            compass_angle = (compass_angle + 360) % 360  # Convert to positive values
                            if deg - 60 <= compass_angle <= deg + 60:
                                values.append(matrix[o, j])
                #average value of the radius  for non-zero cells
                avg_value = sum(values) / len(values) if values else 0
                station_values.append(avg_value)
                r_val = []
                #collect road-type value
                for b in range(road_array.shape[0]):
                    for n in range(road_array.shape[1]):
                        distance = calculate_distance((row, col), (b, n))
                        if distance <= radius and road_array[b, n] != 0:
                                r_val.append(road_array[b, n])
                #average value of the radius  for non-zero cells
                avg = sum(r_val) / len(r_val) if r_val else 0
                road_values.append(avg)

            # Appends the row of averaged stations values
            road_df.loc[len(road_df)] = road_values
            new_df.loc[len(new_df)] = station_values
            print(f'Station values appended: {station_values}')
            print(f'Road values appended: {road_values}')

        else:
            print("no data")

    new_df.to_csv(fr'C:\Users\Austin\Downloads\Capstone\Model Data\Merge2\{city[0]}_road_save.csv')

    #print(new_df)
    database = fr'C:\Users\Austin\Downloads\Capstone\Model Data\Merge2\{city[0]}.csv'
    df4 = pd.read_csv(database)
    # Append the new DataFrame to the original DataFrame
    df = pd.concat([df4, new_df], axis=1)

    df5 = pd.concat([df, road_df], axis=1)
    df5.to_csv(fr'C:\Users\Austin\Downloads\Capstone\Model Data\Merge2\{city[0]}_set.csv')