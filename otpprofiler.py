#!/usr/bin/python

import psycopg2, psycopg2.extras
import urllib2, time, itertools, json
import subprocess, urllib, random

DATE = '08/14/2012'
# split out base and specific endpoint
URL_BASE = "http://localhost:8080/opentripplanner-api-webapp/ws/"
URL_PLAN = URL_BASE + 'plan?'
URL_META = URL_BASE + 'metadata'
SHOW_PARAMS = False
SHOW_URL = False


def getGitInfo(directory=None):
    """Get information about the git repository in specified directory, or of an OTP server if
    no directory is specified. Returns a tuple of (sha1, version) where sha1 is the hash of the 
    HEAD commit, and version is the output of 'git describe', which includes the last tag and how 
    many commits have been made on top of that tag.
    """
    if directory != None :
        try:
            os.chdir(directory)
            sha1 = subprocess.check_output(['git', 'rev-parse', 'HEAD']).strip()
            version = subprocess.check_output(['git', 'describe', 'HEAD'])
        except :
            print "Error reading git info from directory", directory
            return None
    else :
        try :
            req = urllib2.Request(URL_META)
            req.add_header('Accept', 'application/json')
            response = urllib2.urlopen(req)
            if response.code != 200 :
                print "Server metadata response was not 200"
                return None
            content = response.read()
            objs = json.loads(content)['serverVersion']
            version = objs['version']
            sha1 = objs['commit']
        except : 
            print "Error requesting metadata from server. Is it running?"
            return None
    print "sha1 of commit is:", sha1
    print "version of OTP is:", version
    return (sha1, version)
                      
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
        'start_time' : time.asctime(time.gmtime(itinerary['startTime'] / 1000)) + ' GMT',
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
    # replace with sqlAlchemy?
    try:
        # create separate connection for reading, to allow use of both a server-side cursor
        # and progressive commits
        read_conn = psycopg2.connect("dbname='otpprofiler'")
        read_cur = read_conn.cursor('read_cur', cursor_factory=psycopg2.extras.DictCursor)
        write_conn = psycopg2.connect("dbname='otpprofiler'")
        write_cur = write_conn.cursor()
    except:
        print "Unable to connect to the database. Exiting."
        exit(-1)

    gitInfo = getGitInfo()
    if gitInfo == None :
        print "Failed to identify OTP version. Exiting."
        exit(-2)
    write_cur.execute("INSERT INTO runs (git_sha1, run_began, run_ended, git_describe, automated)"
                "VALUES (%s, now(), NULL, %s, TRUE) RETURNING run_id", gitInfo)
    write_conn.commit() # commit to make sure now() is evaluated before run starts                
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
        WHERE origins.endpoint_id < targets.endpoint_id AND 
              origins.random = targets.random AND 
              (requests.typical IS TRUE OR origins.random IS FALSE); """
    read_cur.execute(PARAMS_SQL)
    all_params = read_cur.fetchall()
    random.shuffle(all_params)
    n = 0
    N = len(all_params)
    t0 = time.time()
    for params in all_params : # fetchall takes time and mem, use a server-side named cursor
        n += 1
        t = (time.time() - t0) / 60.0
        T = (N * t) / n
        print "Request %d/%d, time %0.2f min of %0.2f (estimated) " % (n, N, t, T)
        params = dict(params) # could also use a RealDictCursor
        request_id = params.pop('request_id')
        oid = params.pop('oid')
        tid = params.pop('tid')
        # not necessary if OD properly constrained in SQL 
        #if oid == tid :
        #    continue
        params['date'] = DATE
        # Tomcat server + spaces in URLs -> HTTP 505 confusion
        url = URL_PLAN + urllib.urlencode(params)
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
        n_itin = 0
        if response.code != 200 :
            print "not 200"
            status = 'failed'
        else :
            try :
                content = response.read()
                objs = json.loads(content)
                itineraries = objs['plan']['itineraries']
                n_itin = len(itineraries)
                print n_itin, 'itineraries'
                # check response for timeout flag
                status = 'complete'
                # status = 'timed out'
            except :
                print 'no itineraries'
                status = 'no paths'
                
        row = { 'run_id' : run_id,
                'request_id' : request_id,
                'origin_id' : oid,
                'target_id' : tid,
                'total_time' : str(elapsed) + ' seconds',
                'avg_time' : None if n_itin == 0 else '%f seconds' % (float(elapsed) / n_itin),
                'status' : status,
                'membytes' : None }
        response_id = insert (write_cur, 'responses', row, returning='response_id') 
        
        # Create a row for each itinerary within this single trip planner result
        if (n_itin > 0) :
            for (itinerary_number, itinerary) in enumerate(itineraries) :
                row = summarize (itinerary)
                row['response_id'] = response_id
                row['itinerary_number'] = itinerary_number + 1
                insert (write_cur, 'itineraries', row) # no return (automatic serial key) value needed
        write_conn.commit()
    
    write_cur.execute( "UPDATE runs SET run_ended=now() WHERE run_id=%s", (run_id,) )
    write_conn.commit()
    
if __name__=="__main__":
    # parse args
    run()


