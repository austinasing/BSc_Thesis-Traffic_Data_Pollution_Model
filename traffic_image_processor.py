import csv
import ast
import gdal
import math
import numpy as np
import rasterio.crs
import rasterio

cities = ['Ams', 'Rot', 'DnH', 'Utc', 'Edn']

for city in cities:
    out_file = fr'C:\Users\Austin\Downloads\Capstone\Model Data\T4\{city}_t_filterf.csv'
    with open(out_file, 'r') as csvfile:
        n = 0
        # iterate over the rows in the filtered csv
        reader = csv.reader(csvfile)
        for row in reader:

            print(n)
            n += 1

            title = row[0]
            # deletes ss label and extra column on end
            del row[0]
            # del row[-1]

            # converts one long list into an array the correct size for the image
            def list_to_2d_array(row, length, width):
                if length * width != len(row):
                    return None
                    print('Wrong res')
                else:
                    return [row[i:i + width] for i in range(0, len(row), width)]

            # know the size from the ss details
            length = 654
            width = 1024

            arr = list_to_2d_array(row, length, width)

            # erase the white block on the left
            for i in range(len(arr)):
                arr[i] = arr[i][76:]

            print(f'height: {len(arr)}')
            print(f'width: {len(arr[0])}')

            arr2 = []

            # converts weird formatting list thing (issue with '[r,g,b]' strings that should've been lists)
            for row in arr:
                new_row = []
                for pixel in row:
                    new_row.append(ast.literal_eval(pixel))
                arr2.append(new_row)

            # determined previously (might add more for better image processing
            colors = [
                [99, 214, 104],  # green1
                [255, 151, 77],  # orange2
                [242, 60, 50],  # red3
                [129, 31, 31]  # darkr4
            ]
            # colors currently min / maxed normalized
            classes = [
                0.001,
                0.333,
                0.666,
                1
            ]

            min_distance = 10

            # vector distance calculation
            def distance(point1, point2):
                return math.sqrt(
                    (point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2 + (point1[2] - point2[2]) ** 2)

            def assign_colors(pixel):
                for i in range(len(colors)):
                    if distance(pixel, colors[i]) <= min_distance:
                        return classes[i]
                return 0

            # Iterate through the pixels and assign numbers to colors within the minimum distance and 0 to colors outside the minimum distance
            classify = []
            for row in arr2:
                class_row = []
                for pixel in row:
                    class_row.append(assign_colors(pixel))
                classify.append(class_row)

            classified = np.array(classify)

            #need to flatten the array to save it to a csv
            flat_arr = ','.join(classified.flatten().astype(str))

            # append to csv (can keep in numpy do so)
            with open(fr'C:\Users\Austin\Downloads\Capstone\Model Data\T4\{city}_processf.csv', mode = 'a', newline='') as file:
                file.write(flat_arr + '\n')

            print(f"Appended array: {title}")
            print('~~~~~~~~~~')

#then convert into a geotiff and check it out

#define boundary box
#bbox = (4.75331944, 52.29975278, 5.08355, 52.437925)

#transform = rasterio.transform.from_bounds(*bbox, norm_arr.shape[1], norm_arr.shape[0])
#crs = rasterio.crs.CRS.from_epsg(4326)

#filename = r'C:\Users\Austin\Downloads\Capstone\Maps\ams_traff.tif'

#with rasterio.open(filename, 'w', driver='GTiff', width=norm_arr.shape[1], height=norm_arr.shape[0], count=1, dtype=arr.dtype, crs=crs, transform=transform) as dst:
    #dst.write(norm_arr, 1)
