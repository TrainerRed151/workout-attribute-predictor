import os
from parse import parse
from dateutil import parser
from geopy.distance import geodesic


directory_in_str = 'rides/'
directory = os.fsencode(directory_in_str)
lat_long_str = '<trkpt lat="{}" lon="{}">'
ele_str = '<ele>{}</ele>'
time_str = '<time>{}</time>'
hr_str = '<gpxtpx:hr>{}</gpxtpx:hr>'

points = []

for file in os.listdir(directory):
     filename = os.fsdecode(file)
     if filename.endswith('.gpx'):
        file_path = os.path.join(directory.decode(), filename)

        with open(file_path, 'r') as file:
            lines = file.readlines()

        idx = -1
        for line in lines:
            entry = line.strip()
            if 'lat' in entry and 'lon' in entry:
                lat, long = parse(lat_long_str, entry)
                lat = float(lat)
                long = float(long)

                idx += 1
                points.append({'lat': lat, 'long': long})
            elif '<ele>' in entry:
                ele = parse(ele_str, entry)
                points[idx]['ele'] = float(ele[0])
            elif '<time>' in entry and idx >= 0:
                time = parse(time_str, entry)
                time = parser.parse(time[0])
                points[idx]['time'] = time
            elif '<gpxtpx:hr>' in entry:
                hr = parse(hr_str, entry)
                points[idx]['hr'] = int(hr[0])

X = []
y = []
total_time = 0
elevation_gain = 0
for i in range(len(points)):
    if i == 0:
        grade = 0
        speed = 0
        dist = 0
        time = 0
    else:
        grade = points[i]['ele'] - points[i-1]['ele']
        dist = geodesic((points[i]['lat'], points[i]['long']), (points[i-1]['lat'], points[i-1]['long'])).feet + grade
        time = (points[i]['time'] - points[i-1]['time']).total_seconds()
        speed = dist/time

    total_time += time
    elevation_gain += grade

    X.append([total_time, elevation_gain, speed, grade])
    y.append(points[i]['hr'])


