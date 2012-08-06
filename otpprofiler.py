#!/usr/bin/python

import psycopg2, psycopg2.extras
import urllib2, time, itertools, json
import subprocess

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

# get git information
sha1 = subprocess.check_output(['git', 'rev-parse', 'HEAD']).strip()
assert(len(sha1) == 40)
version = 'none'
try:
    version = subprocess.check_output(['git', 'describe', 'HEAD'])
except:
    pass

cur.execute("INSERT INTO runs (git_sha1, run_began, run_ended, git_describe, automated)" +
    "VALUES (%s, now(), now(), %s, TRUE) RETURNING run_id", (sha1, version))
run_id = cur.fetchone()[0]
print "run id", run_id

# could also use select/join and server-side cursor for enumerating requests

# use automatic dict mapping for params (see nn)
URL = "http://localhost:8080/opentripplanner-api-webapp/ws/plan?submit&fromPlace=%s,%s&toPlace=%s,%s&min=%s&maxWalkDistance=%d&mode=%s&submit&time=%s&date=%s&arr=%s"
# fetch rows as dictionary; naming the cursor causes it to be a server-side cursor
cur_params = conn.cursor('cur_params', cursor_factory=psycopg2.extras.DictCursor)
cur_params.execute("SELECT * FROM requests")
for params in cur_params :
    # set params into dict ...
    for (origin, target) in itertools.product(endpoints, endpoints) :
        if origin == target :
            continue
        url = URL % (origin['lat'], origin['lon'], target['lat'], target['lon'], params['min'], 
            params['maxwalkdistance'], params['modes'], params['time'], DATE, params['arriveby'])
        print url, "...",
        req = urllib2.Request(url)
        req.add_header('Accept', 'application/json')
        start_time = time.time()
        response = urllib2.urlopen(req)
        end_time = time.time()
        elapsed = end_time - start_time
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
        cur.execute("INSERT INTO results (run_id, request_id, origin_id, target_id, response_time, membytes)" +
            "VALUES (%s, %s, %s, %s, %s, %s) RETURNING result_id", 
            (run_id, params['request_id'], origin['endpoint_id'], target['endpoint_id'], str(elapsed) + 'sec', 0))
        result_id = cur.fetchone()[0]
        itinerary_number = 0
        for itinerary in itineraries :
            n_legs = 0
            n_vehicles = 0
            walk_distance = 0
            wait_time_sec = 0
            ride_time_sec = 0
            start_time = "2012-01-01 8:00"
            duration = 0
            cur.execute("INSERT INTO itineraries (result_id, itinerary_number, n_legs, n_vehicles, " +
                "walk_distance, wait_time_sec, ride_time_sec, start_time, duration) VALUES " +
                "(%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING result_id", 
                (result_id, itinerary_number, n_legs, n_vehicles, walk_distance, wait_time_sec, 
                ride_time_sec, start_time, str(duration) + ' sec'))
            itinerary_number  += 1
        conn.commit()



