#!/usr/bin/python

import psycopg2, psycopg2.extras
import urllib2, time, itertools, json
import subprocess, urllib

DATE = '08/14/2012'
# split out base and specific endpoint
URL = "http://localhost:8080/opentripplanner-api-webapp/ws/plan?"
SHOW_PARAMS = True
SHOW_URL = True


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
    # store version number subelements in separate fields, request from server not filesystem.
    
    
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
    
    
def sqlarray (list):
    return '{%s}' % (','.join(list))


def summarize (itinerary) :
    routes = []
    trips = []
    waits = []
    n_vehicles = 0
    n_legs = 0
    for leg in itinerary['legs'] :
        n_legs += 1
        if 'route' in leg and len(leg['route']) > 0 :
            routes.append(leg['route'])
            n_vehicles += 1
        #trips.append(leg['trip'])
        #waits.append(leg['wait'])
    ret = { 
        'start_time' : time.asctime(time.gmtime(itinerary['startTime'] / 1000)),
        'duration' : '%d msec' % int(itinerary['duration']),
        'n_legs' : n_legs,
        'n_vehicles' : n_vehicles,
        'walk_distance' : itinerary['walkDistance'],
        'wait_time_sec' : itinerary['waitingTime'],
        'ride_time_sec' : itinerary['transitTime'],
        'routes' : sqlarray(routes),
        'trips' : sqlarray(trips),
        'waits' : sqlarray(waits) }
    return ret
    

def run() :
    # depends on peer authentication
    try:
        # create separate connection for reading, to allow use of both a server-side cursor
        # and progressive commits
        read_conn = psycopg2.connect("dbname='otpprofiler'")
        read_cur = read_conn.cursor('read_cur', cursor_factory=psycopg2.extras.DictCursor)
        write_conn = psycopg2.connect("dbname='otpprofiler'")
        write_cur = write_conn.cursor()
    except:
        print "unable to connect to the database"
        exit(-1)

    write_cur.execute("INSERT INTO runs (git_sha1, run_began, run_ended, git_describe, automated)"
                "VALUES (%s, now(), NULL, %s, TRUE) RETURNING run_id", getGitInfo())
    run_id = write_cur.fetchone()[0]
    print "run id", run_id

    # note double quotes in SQL string to force case-sensitivity on query param columns.
    # origin/destination matrix is constrained to be lower-triangular since we do both 
    # depart-after and arrive-by searches. this halves the number of searches.
    # the set of all combinations is filtered such that only the 'typical' requests (i.e. tuples of
    # query parameters) are combined with the (more numerous) random endpoints, but all reqests are 
    # combined with the (presumably less numerous) explicitly defined endpoints.
    # that is, in every combination retained, the request is either considered typical, or in the
    # case that the request is atypical, the endpoints are not random. 
    # only like pairs of endpoints are considered (random to random, nonrandom to nonrandom).
    PARAMS_SQL = """ SELECT requests.*,
        origins.endpoint_id AS oid, origins.lat || ',' || origins.lon AS "fromPlace",
        targets.endpoint_id AS tid, targets.lat || ',' || targets.lon AS "toPlace"
        FROM requests, endpoints AS origins, endpoints AS targets
        WHERE oid < tid AND 
              origins.random = destinations.random AND 
              (requests.typical IS TRUE OR origins.random IS FALSE); """
    read_cur.execute(PARAMS_SQL)
    for params in read_cur : # fetchall takes time and mem, use a server-side named cursor
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
        response_id = insert (write_cur, 'responses', row, returning='response_id') 
        # Create a row for each itinerary within this single trip planner result
        for (itinerary_number, itinerary) in enumerate(itineraries) :
            row = summarize (itinerary)
            row['response_id'] = response_id
            row['itinerary_number'] = itinerary_number
            insert (write_cur, 'itineraries', row) # no return (automatic serial key) value needed
        write_conn.commit()


if __name__=="__main__":
    # parse args
    run()


