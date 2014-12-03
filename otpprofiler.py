#!/usr/bin/python

import urllib2, time, itertools, json
import subprocess, urllib, random
import simplejson
import pprint
from copy import copy

DATE = '11/12/2014'
# split out base and specific endpoint
SHOW_PARAMS = True
SHOW_URL = False

def cycle(seq):
    "A generator that loops over a sequence forever."
    # Strangely, there seems to be no library function to do this.
    # https://docs.python.org/3.4/library/itertools.html#itertools.cycle
    # has to make a copy of every element in the iterator to obey the iterator interface.
    while True:
        for elem in seq:
            yield elem

def pairs(iterable):
    "A generator that takes items from a sequence two at a time. (s0, s1), (s2, s3), (s4, s5), ..."
    it = iter(iterable)
    for x in it:
        yield (x, next(it, None))


def get_params(fast):
    requests_json = simplejson.load(open("requests.json"))
    requests = requests_json['requests']
    endpoints = requests_json['endpoints']
    # Make sure there is an even number of endpoints
    if len(endpoints) % 2 != 0 :
        endpoints = endpoints[:-1]
    ret = []
    # if fast :
    # else :
    for (request, (origin, target)) in zip(cycle(requests), pairs(endpoints)):
        req = copy(request)
        req['oid'] = origin['id']
        req['tid'] = target['id']
        req['fromPlace'] = "%s,%s"%(origin['lat'],origin['lon'])
        req['toPlace']   = "%s,%s"%(target['lat'],target['lon'])
        ret.append( req )
        print req
    # TODO yield
    return ret

def getServerInfo(host):
    """Get information about the server that is being profiled. Returns a tuple of:
    (sha1, version, cpuName, nCores)
    where sha1 is the hash of the HEAD commit, version is the output of 'git describe' (which 
    includes the last tag and how many commits have been made on top of that tag), 
    cpuName is the model of the cpu as reported by /proc/cpuinfo via the OTP serverinfo API,
    and nCores is the number of (logical) cores reported by that same API, including hyperthreading. 
    """
    url_meta = "http://"+host+"/otp/"

    try :
        print "grabbing metadata from %s"%url_meta
        req = urllib2.Request(url_meta)
        req.add_header('Accept', 'application/json')
        response = urllib2.urlopen(req)
        if response.code != 200 :
            print "Server metadata response was not 200"
            return None
        content = response.read()
        objs = json.loads(content)
        print "Server metadata response: ", objs
        version = objs['serverVersion']['version']
        sha1 = objs['serverVersion']['commit']
        # would also be nice to have build date
        cpuName = objs['cpuName']
        nCores = objs['nCores']
    except urllib2.URLError : 
        # This is a normal condition while waiting for server to come up, trap exception and return None.
        # Any problem with decoding the server response will still blow up the program with an exception.
        print "Error requesting metadata from OTP server. Is it running?"
        return None
    print "sha1 of commit is:", sha1
    print "version of OTP is:", version
    print "processor type is:", cpuName
    print "number of logical cores is:", nCores
    return (sha1, version, cpuName, nCores)

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
    
def run(connect_args) :
    "This is the principal function..."
    notes = connect_args.pop('notes')
    retry = connect_args.pop('retry')
    fast  = connect_args.pop('fast')
    host = connect_args.pop('host')
    info = getServerInfo(host)
    while retry > 0 and info == None:
        print "Failed to connect to OTP server. Waiting to retry (%d)." % retry
        time.sleep(10)
        info = getServerInfo(host)
        retry -= 1
        
    if info == None :
        print "Failed to identify OTP version. Exiting."
        exit(-2)

    # Create a dict describing this particular run of the profiler, which will be output as JSON
    run_time_id = int(time.time())
    run_row = info + (notes, run_time_id)
    run_json = dict(zip(('git_sha1','git_describe','cpu_name','cpu_cores','notes','id'), run_row))

    all_params = get_params(fast)

    random.shuffle(all_params)
    n = 0
    N = len(all_params)
    t0 = time.time()
    response_json = []
    full_itins_json = []
    pp = pprint.PrettyPrinter(indent=4)
    for params in all_params : 
        n += 1
        t = (time.time() - t0) / 60.0
        T = (N * t) / n
        print "Request %d/%d, time %0.2f min of %0.2f (estimated) " % (n, N, t, T)
        params = dict(params) # TODO necessary? 
        request_id = params.pop('id')
        oid = params.pop('oid')
        tid = params.pop('tid')
        params['date'] = DATE
        params['numItineraries'] = 3
        # Tomcat server + spaces in URLs -> HTTP 505 confusion
        qstring = urllib.urlencode(params)
        url = "http://"+host+"/otp/routers/default/plan?" + qstring
        if SHOW_PARAMS :
            pp.pprint(params)
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
            content = response.read()
            objs = json.loads(content)

            if 'plan' in objs:
                itineraries = objs['plan']['itineraries']
                n_itin = len(itineraries)
                print n_itin, 'itineraries'
                # check response for timeout flag
                status = 'complete'
                path_times = objs['debugOutput']['pathTimes']
                print path_times
                # status = 'timed out'
            else:
                print 'no itineraries'
                status = 'no paths'
                
        row = { 'url' : url,
                'run_id' : run_time_id,
                'request_id' : request_id,
                'origin_id' : oid,
                'target_id' : tid,
                'id_tuple' : "%s-%s-%s"%(oid,tid,request_id),
                'total_time' : str(elapsed) + ' seconds',
                'avg_time' : None if n_itin == 0 else '%f seconds' % (float(elapsed) / n_itin),
                'status' : status,
                'membytes' : None }
        response_id = len(response_json)
        row['response_id'] = response_id
        row['itins'] = []
        response_json.append( row )
        
        
        # Create a row for each itinerary within this single trip planner result
        if (n_itin > 0) :
            for (itinerary_number, itinerary) in enumerate(itineraries) :
                itin_row = summarize (itinerary)
                #itin_row['response_id'] = response_id
                itin_row['itinerary_number'] = itinerary_number + 1
                
                full_itin = {'response_id':response_id,'itinerary_number':itinerary_number+1}
                full_itin['body']=itinerary
                full_itins_json.append( full_itin )

                row['itins'].append( itin_row )
        pp.pprint(row)

    fpout = open("run_summary.%s.json"%run_time_id,"w")
    run_json['responses'] = response_json
    simplejson.dump(run_json, fpout, indent=2)
    fpout.close()

    fpout = open("full_itins.%s.json"%run_time_id,"w")
    simplejson.dump( full_itins_json, fpout, indent=2 )
    fpout.close()
    
import argparse
if __name__=="__main__":
    import argparse # optparse is deprecated
    parser = argparse.ArgumentParser(description='perform an otp profiler run') 
    parser.add_argument('host') 
    parser.add_argument('-f', '--fast', action='store_true', default=False) 
    parser.add_argument('-n', '--notes') 
    parser.add_argument('-r', '--retry', type=int, default=5) 
    args = parser.parse_args() 

    # args is a non-iterable, non-mapping Namespace (allowing usage in the form args.name), 
    # so convert it to a dict before passing it into the run function.
    run(vars(args))


