import os
from parse import parse
from dateutil import parser
from geopy.distance import geodesic
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score
from sklearn.utils import shuffle


predict_file = 'test.gpx'
out_file = 'test2.gpx'

#directory_in_str = 'rides/'
directory_in_str = 'runs/'
directory = os.fsencode(directory_in_str)
lat_long_str = '<trkpt lat="{}" lon="{}">'
ele_str = '<ele>{}</ele>'
time_str = '<time>{}</time>'
hr_str = '<gpxtpx:hr>{}</gpxtpx:hr>'
hr_insert = '''    <extensions>
     <gpxtpx:TrackPointExtension>
      <gpxtpx:hr>{}</gpxtpx:hr>
     </gpxtpx:TrackPointExtension>
    </extensions>
'''


def get_points(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    points = []
    total_time = 0
    elevation_gain = 0

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
            points[idx]['time_str'] = time[0]
            time = parser.parse(time[0])
            points[idx]['time'] = time
        elif '<gpxtpx:hr>' in entry:
            hr = parse(hr_str, entry)
            points[idx]['hr'] = int(hr[0])

    return points


def get_Xy(points, training=False):
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
            ev_change = 0
        else:
            ev_change = points[i]['ele'] - points[i-1]['ele']
            grade = 0
            for j in range(max(i-10, 0), i):
                grade += (points[i]['ele'] - points[j]['ele'])
            grade = grade/min(i, 10)
            dist = geodesic((points[i]['lat'], points[i]['long']), (points[i-1]['lat'], points[i-1]['long'])).meters
            time = (points[i]['time'] - points[i-1]['time']).total_seconds()
            speed = dist/time

        total_time += time
        elevation_gain += max(ev_change, 0)

        X.append([total_time, elevation_gain, speed, grade, ev_change])
        if training:
            y.append(points[i]['hr'])
        else:
            y.append(points[i]['time_str'])

    return X, y


def create_file(out_file, predict_file, y, time_list):
    with open(predict_file, 'r') as file:
        lines = file.readlines()

    with open(out_file, 'w') as file:
        start = True
        for line in lines:
            if '<gpxtpx' in line or '<extensions' in line:
                continue
            if '</gpxtpx' in line or '</extensions' in line:
                continue

            file.write(line)

            entry = line.strip()
            if 'lat' in entry and 'lon' in entry:
                start = False

            if '<time>' in entry and not start:
                time = parse(time_str, entry)
                idx = time_list.index(time[0])
                hr = y[idx]
                file.write(hr_insert.format(hr))


def main():
    X = []
    y = []
    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        if not filename.endswith('.gpx'):
            continue

        file_path = os.path.join(directory.decode(), filename)
        points = get_points(file_path)
        Xtemp, ytemp = get_Xy(points, training=True)
        X.extend(Xtemp)
        y.extend(ytemp)

    X, y = shuffle(X, y, random_state=0)
    regr = RandomForestRegressor(random_state=0, n_estimators=100)
    print(cross_val_score(regr, X, y, cv=5))
    regr.fit(X, y)
    print(regr.feature_importances_)

    points = get_points(predict_file)
    X2, time_list = get_Xy(points)
    y2 = regr.predict(X2)
    print(f"{min(y2)} -- {sum(y2)/len(y2)} -- {max(y2)}")

    create_file(out_file, predict_file, y, time_list)


if __name__ == '__main__':
    main()
