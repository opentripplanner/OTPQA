from __future__ import print_function

import random
import sys

import numpy as np
import unicodecsv
import utm
from sklearn.cluster import DBSCAN


def clusterEndpoints(orig_endpoints, eps=2500, min_samples=2, return_outliers=True):
    coords = []
    coordhits = []
    for i, l in enumerate(orig_endpoints):
        name = l['name']
        lon = l['lon']
        lat = l['lat']
        hits = l['hits'] if 'hits' in l else 0

        lat = float(lat)
        lon = float(lon)

        utm35_coordinates = utm.from_latlon(lat, lon, 35)
        x = utm35_coordinates[0]
        y = utm35_coordinates[1]

        x += random.uniform(-50, 50)
        y += random.uniform(-50, 50)

        coords.append((x, y))
        coordhits.append((hits,))

    coords = np.array(coords)
    coordhits = np.array(coordhits)

    db = DBSCAN(eps=eps, min_samples=min_samples, algorithm='auto', metric='euclidean').fit(coords)
    coords = np.hstack((coords,coordhits))
    cluster_labels = db.labels_
    n_clusters = len(set(cluster_labels))
    print('Clustered. Num clusters:', n_clusters)
    clusters = (coords[cluster_labels == n] for n in range(-1, n_clusters))

    outliers = next(clusters)

    endpoints = []
    if return_outliers:
        for o in outliers:
            if np.isnan(o[0]):
                continue
            lat, lon = utm.to_latlon(o[0], o[1], 35, 'N')

            endpoints.append({'name': 'o%d' % len(endpoints), 'lon': lon, 'lat': lat,'hits':o[2]})

    for c in clusters:
        if len(c) == 0:
            continue
        cp = np.nanmean(c, axis=0)
        hitsum = np.sum(c[:,2])
        if np.isnan(cp[0]):
            continue
        lat, lon = utm.to_latlon(cp[0], cp[1], 35, 'N')

        endpoints.append({'name': 'c%d' % len(endpoints), 'lon': lon, 'lat': lat,'hits':hitsum})

    return endpoints


if __name__ == '__main__':
    f = open(sys.argv[1], 'rb')
    r = unicodecsv.DictReader(f, encoding='utf-8')

    endpoints = clusterEndpoints(r)
    f.close()

    f = open(sys.argv[1] + '.clustered', 'wb')
    w = unicodecsv.writer(f, encoding='utf-8')
    w.writerow(('name', 'lon', 'lat'))

    for ep in endpoints:
        w.writerow((ep['name'], ep['lon'], ep['lat']))

    f.close()
