#!/usr/bin/python2.4

import psycopg2, itertools

# connect to database
# presumably we are using peer authentication and logged in as a user who has a pgsql account
try:
    conn = psycopg2.connect("dbname='otpprofiler'")
except:
    print "unable to connect to the database"
    exit(-1)
    
# Initialize the otpprofiler DB 'requests' table with query parameters
# FIXME: this is creating requests for varying walk distances with walk and bike modes, which are meaningless    
times = ["%02d:%02d:00" % (h, m) for h in range(5, 24, 2) for m in range(0, 60, 30)]
walks = [500, 1000, 2000, 3000, 5000, 10000, 2000000]
modes = ["WALK,TRANSIT", "BICYCLE,TRANSIT", "WALK", "BICYCLE"]
mins = ["QUICK"]
arriveBys = (True, False)

params = list(itertools.product(times, walks, modes, mins, arriveBys))

cur = conn.cursor()
cur.executemany("INSERT INTO requests (time, maxWalkDistance, modes, min, arriveBy) VALUES (%s, %s, %s, %s, %s)", params)
conn.commit()

# Initialize the otpprofiler DB with random endpoints and user-defined endpoints

import csv
cur = conn.cursor()
for filename in ["endpoints_random.csv"] : #, "endpoints.csv"] :
    endpoints = open(filename)
    reader = csv.DictReader(endpoints)
    sql = "INSERT INTO endpoints (random, lon, lat, name, notes) VALUES (true, %(lon)s, %(lat)s, 'rand'||%(n)s, %(name)s )"
    for line in reader :
        cur.execute(sql, line)
conn.commit()

