#!/usr/bin/python2.4

import psycopg2, itertools

# connect to database
# presumably we are using peer authentication and logged in as a user who has a pgsql account
try:
    conn = psycopg2.connect("dbname='otpprofiler'")
except:
    print "unable to connect to the database"
    exit(-1)
    
# Initialize the otpprofiler DB 'requests' table with query parameters.
# Note that on-street modes are not walk-limited, so we don't want to vary the max walk param there.
# another way to do this would be to store the various values in tables, and construct this
# view as a constraned product of all the other tables (probably eliminating the synthetic keys)
times = ["%02d:%02d:00" % (h, m) for h in [7, 9, 14, 23] for m in [55, 25]]
walk_limited_modes = ( ["WALK,TRANSIT", "BICYCLE,TRANSIT"], [250, 2000, 40000] )
non_walk_limited_modes = ( ["WALK", "BICYCLE"], [2000] )
mins = ["QUICK"]
arriveBys = (True, False)

cur = conn.cursor()
for modes, walks in (walk_limited_modes, non_walk_limited_modes) :
    params = itertools.product(times, walks, modes, mins, arriveBys)
    # NOTE the use of double quotes to force case-sensitivity for column names. These columns 
    # represent query parameters that will be substituted directly into URLs, and URLs are defined 
    # to be case-sensitive.  
    cur.executemany("""INSERT INTO requests (time, "maxWalkDistance", mode, min, "arriveBy", typical) 
        VALUES (%s, %s, %s, %s, %s, FALSE)""", params)

# designate 'typical' parameter combinations
cur.execute("""UPDATE requests SET typical=TRUE WHERE time='07:55:00' 
    AND "maxWalkDistance"='2000' AND mode != 'BICYCLE,TRANSIT' AND "arriveBy" IS FALSE""")

# Commit the transaction
conn.commit()

# Initialize the otpprofiler DB with random endpoints and user-defined endpoints
import csv
cur = conn.cursor()
for filename, random in [("endpoints_random.csv", True), ("endpoints_custom.csv", False)] :
    endpoints = open(filename)
    reader = csv.DictReader(endpoints)
    sql = """INSERT INTO endpoints (random, lon, lat, name, notes) VALUES (%s, %s, NULL)"""
    sql %= (random, "%(lon)s, %(lat)s, %(name)s" )
    cur.executemany (sql, reader)

# Commit the transaction
conn.commit()

