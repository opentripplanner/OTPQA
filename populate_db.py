#!/usr/bin/python2.4

import psycopg2, itertools
import simplejson

json_out = {}

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
# view as a constrained product of all the other tables (probably eliminating the synthetic keys).

# (time, arriveBy)
times = [ ("08:50:00", True ),
          ("14:00:00", True ),
          ("18:00:00", False),
          ("23:45:00", False) ]

# (mode, walk, min)
modes = [ (mode, walk, "QUICK") 
    for mode in ["WALK,TRANSIT", "BICYCLE,TRANSIT"] 
    for walk in [250, 2000, 40000] ]
modes.append( ("WALK", 2000, "QUICK") )
modes.extend( [("BICYCLE", 2000, minimize) for minimize in ["QUICK", "SAFE", "FLAT"]] )

all_params = [(time, walk, mode, minimize, arriveBy) 
    for (time, arriveBy) in times 
    for (mode, walk, minimize) in modes] 

cur = conn.cursor()
requests_json = []
for i, params in enumerate( all_params ) :
    # NOTE the use of double quotes to force case-sensitivity for column names. These columns 
    # represent query parameters that will be substituted directly into URLs, and URLs are defined 
    # to be case-sensitive.

    time,maxWalkDist,mode,min,arriveBy = params
    typical = (time=="08:50:00" and maxWalkDist == 2000 and "BICYCLE" not in mode)

    cur.execute("""INSERT INTO requests (time, "maxWalkDistance", mode, min, "arriveBy", typical) 
        VALUES (%s, %s, %s, %s, %s, %s)""", params+(typical,))

    requests_json.append( dict(zip(('time','maxWalkDistance','mode','min','arriveBy','typical','id'),params+(typical,i))) )
json_out['requests'] = requests_json

# Commit the transaction
conn.commit()

# Initialize the otpprofiler DB with random endpoints and user-defined endpoints
import csv
cur = conn.cursor()
endpoints_json = []
for filename, random in [("endpoints_random.csv", True), ("endpoints_custom.csv", False)] :
    endpoints = open(filename)
    reader = csv.DictReader(endpoints)
    sql = """INSERT INTO endpoints (random, lon, lat, name, notes) VALUES (%s, %s, NULL)"""
    sql %= (random, "%(lon)s, %(lat)s, %(name)s" )

    endpoints = list(reader)

    cur.executemany (sql, endpoints)


    for i, rec in enumerate( endpoints ):
        endpoint_rec = {'id':i, 'random':random, 'lon':float(rec['lon']), 'lat':float(rec['lat']), 'name':rec['name'], 'notes':None}
        endpoints_json.append( endpoint_rec )
json_out['endpoints'] = endpoints_json

# Commit the transaction
conn.commit()

fpout = open("requests.json","w")
simplejson.dump(json_out, fpout, indent=2 )
fpout.close()

