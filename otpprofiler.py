#!/usr/bin/python

import psycopg2, psycopg2.extras
import urllib2, time, itertools, json

DATE = '08/14/2012'

# depends on peer authentication
try:
    conn = psycopg2.connect("dbname='otpprofiler'")
except:
    print "unable to connect to the database"
    exit(-1)

# fetch endpoint rows as dictionary
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
cur.execute("SELECT * FROM endpoints")
endpoints = cur.fetchall();

# could also use select/join and server-side cursor for enumerating requests

URL = "http://localhost:8080/opentripplanner-api-webapp/ws/plan?submit&fromPlace=%s,%s&toPlace=%s,%s&min=%s&maxWalkDistance=%d&mode=%s&submit&time=%s&date=%s&arr=%s"
# fetch rows as dictionary; naming the cursor causes it to be a server-side cursor
cur = conn.cursor('cur_requests', cursor_factory=psycopg2.extras.DictCursor)
cur.execute("SELECT * FROM requests")
for row in cur :
    for (origin, target) in itertools.product(endpoints, endpoints) :
        if origin == target :
            continue
        url = URL % (origin['lat'], origin['lon'], target['lat'], target['lon'], row['min'], row['maxwalkdistance'], row['modes'], row['time'], DATE, row['arriveby'])
        print url, "... ",
        req = urllib2.Request(url)
        req.add_header('Accept', 'application/json')
        start = time.time()
        response = urllib2.urlopen(req)
        end = time.time()
        duration = end - start
        print response.code
        if response.code != 200 :
            continue
        try :
            content = response.read()
            objs = json.loads(content)
            itineraries = objs['plan']['itineraries']
        except :
            print 'no itineraries'
            continue
        # totalRunTime += duration
        
