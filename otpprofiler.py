#!/usr/bin/python

import psycopg2, psycopg2.extras
import urllib2, time, itertools, json
import subprocess, urllib

DATE = '08/14/2012'
URL = "http://localhost:8080/opentripplanner-api-webapp/ws/plan?"
SHOW_PARAMS = True
SHOW_URL = False
# depends on peer authentication
try:
    conn = psycopg2.connect("dbname='otpprofiler'")
    cur = conn.cursor()
except:
    print "unable to connect to the database"
    exit(-1)

def getGitInfo(directory=None):
    """Get information about the git repository in the current (or specified) directory.
    Returns a tuple of (sha1, version) where sha1 is the hash of the HEAD commit, and version
    is the output of 'git describe', which includes the last tag and how many commits have been made
    on top of that tag.
    """
    if directory != None :
        os.chdir(directory)
    sha1 = subprocess.check_output(['git', 'rev-parse', 'HEAD']).strip()
    assert(len(sha1) == 40)
    try:
        version = subprocess.check_output(['git', 'describe', 'HEAD'])
    except:
        version = None
    return (sha1, version)
    
cur.execute("INSERT INTO runs (git_sha1, run_began, run_ended, git_describe, automated)"
            "VALUES (%s, now(), NULL, %s, TRUE) RETURNING run_id", getGitInfo())
run_id = cur.fetchone()[0]
print "run id", run_id

def insert (cursor, table, d, returning=None) :
    """Convenience method to insert all key-value pairs from a Python dictionary into a table
    interpreting the dictionary keys as column names. Can optionally return a column from the
    inserted row. This is useful for getting the automatically generated serial ID of the new row.
    """
    # keys and values are guaranteed to be in the same order by python
    colnames = ','.join(d.keys())
    placeholders = ','.join(['%s' for _ in d.values()])
    sql = "INSERT INTO %s (%s) VALUES (%s)" % (table, colnames, placeholders) 
    if returning != None :
        sql += " RETURNING %s" % (returning)
    cursor.execute(sql, d.values())
    if returning != None :
        result = cursor.fetchone()
        return result[0]
    
# note double quotes in SQL string to force case-sensitivity
PARAMS_SQL = """ SELECT requests.*,
    origins.endpoint_id AS oid, origins.lat || ',' || origins.lon AS "fromPlace",
    targets.endpoint_id AS tid, targets.lat || ',' || targets.lon AS "toPlace"
    FROM requests, endpoints AS origins, endpoints AS targets; """
params_cur = conn.cursor('params_cur', cursor_factory=psycopg2.extras.DictCursor)
# here we should be applying a WHERE clause based on some command line parameters to allow shorter runs
params_cur.execute(PARAMS_SQL)
for params in params_cur : # fetchall takes time and mem, use a server-side named cursor
    params = dict(params) # could also use a RealDictCursor
    request_id = params.pop('request_id')
    oid = params.pop('oid')
    tid = params.pop('tid')
    if oid == tid :
        continue
    params['date'] = DATE
    # Tomcat server + spaces in URLs -> HTTP 505 confusion
    url = URL + urllib.urlencode(params)
    if SHOW_PARAMS :
        print params
    if SHOW_URL :
        print url
    req = urllib2.Request(url)
    req.add_header('Accept', 'application/json')
    start_time = time.time()
    response = urllib2.urlopen(req)
    end_time = time.time()
    elapsed = end_time - start_time
    if response.code != 200 :
        print "not 200"
        continue
    try :
        content = response.read()
        objs = json.loads(content)
        itineraries = objs['plan']['itineraries']
    except :
        print 'no itineraries'
        continue
    print len(itineraries), 'itineraries'
    row = { 'run_id' : run_id,
            'request_id' : request_id,
            'origin_id' : oid,
            'target_id' : tid,
            'response_time' : str(elapsed) + 'sec',
            'membytes' : 0 }
    result_id = insert (cur, 'results', row, returning='result_id') 
    # Create a row for each itinerary within this single trip planner result
    for (itinerary_number, itinerary) in enumerate(itineraries) :
        row = { 'result_id' : result_id,
                'itinerary_number' : itinerary_number,
                'n_legs' : 0,
                'n_vehicles' : 0,
                'walk_distance' : 0,
                'wait_time_sec' : 0,
                'ride_time_sec' : 0,
                'start_time' : "2012-01-01 8:00",
                'duration' : '%d sec' % 0 }
        insert (cur, 'itineraries', row) # no return (automatic serial key) value needed

# Commit in one giant transaction
conn.commit()



