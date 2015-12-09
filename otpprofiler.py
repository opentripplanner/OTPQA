#!/usr/bin/python

import urllib2, time, itertools, json
import subprocess, urllib, random
import simplejson
import pprint
from copy import copy
# python-requests no longer has first-class support for concurrent asynchronous HTTP requests
# the author has moved it to https://github.com/kennethreitz/grequests
# python-requests wraps urllib2 providing a much nicer API.
import grequests

DATE = '2015-12-30'
# split out base and specific endpoint
SHOW_PARAMS = False
SHOW_URL = False
SHOW_RESPONSE = False

# globals to store accumulated responses. one file for summaries, one file for full itineraries.
response_json = []
full_itins_json = []
pp = pprint.PrettyPrinter(indent=4)
n = 0 # number of responses received
N = 0 # total number of responses expected
t0 = 0 # time that search begins

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

# summarize the result for an itinerary planner request
def summarize_plan (itinerary) :
    routes = []
    trips = []
    waits = []
    leg_modes = []
    leg_times = []
    n_vehicles = 0
    n_legs = 0
    for leg in itinerary['legs'] :
        n_legs += 1
        leg_modes.append(leg['mode'])
        leg_times.append((leg['endTime'] - leg['startTime'])/1000)
        if 'route' in leg and len(leg['route']) > 0 :
            routes.append(leg['route'])
            trips.append(leg['tripId'])
            n_vehicles += 1
            wait = (leg['from']['departure'] - leg['from']['arrival'])/1000
            #print(' - wait = %d'%(wait))
            waits.append(wait)
    ret = {
        'start_time' : time.asctime(time.gmtime(itinerary['startTime'] / 1000)) + ' GMT',
        'duration' : '%d sec' % int(itinerary['duration']),
        'n_legs' : n_legs,
        'n_vehicles' : n_vehicles,
        'walk_distance' : itinerary['walkDistance'],
        'wait_time_sec' : itinerary['waitingTime'],
        'ride_time_sec' : itinerary['transitTime'],
        'routes' : routes,
        'trips' : trips,
        'waits' : waits,
        'leg_modes' : leg_modes,
        'leg_times' : leg_times
    }
    return ret

# summarize the result for a profile request
def summarize_profile (option) :
    routes = []
    trips = []
    waits = []
    leg_modes = []
    leg_times = []
    n_vehicles = 0
    n_legs = 0
    wait_time_sec = 0
    ride_time_sec = 0

    if 'transit' in option:
        if 'access' in option:
            n_legs += 1
            summarize_profile_non_transit_leg(option['access'], leg_modes, leg_times)

        for transit_leg in option['transit']:
            n_legs += 1
            n_vehicles += 1
            leg_modes.append(transit_leg['mode'])

            avg_wait_time = transit_leg['waitStats']['avg']
            waits.append(avg_wait_time)
            wait_time_sec += avg_wait_time

            avg_ride_time = transit_leg['rideStats']['avg']
            leg_times.append(avg_ride_time)
            ride_time_sec += avg_ride_time

            if len(transit_leg['routes']) == 1:
                routes.append(transit_leg['routes'][0]['id'])
            else:
                route_ids = []
                for route in transit_leg['routes']:
                    route_ids.append(route['id'])
                routes.append(route_ids)

        if 'egress' in option:
            n_legs += 1
            summarize_profile_non_transit_leg(option['egress'], leg_modes, leg_times)

    else:
        n_legs = 1
        summarize_profile_non_transit_leg(option['access'], leg_modes, leg_times)

    ret = {
        'n_legs' : n_legs,
        'n_vehicles' : n_vehicles,
        'wait_time_sec' : wait_time_sec,
        'ride_time_sec' : ride_time_sec,
        'routes' : routes,
        'waits' : waits,
        'leg_modes' : leg_modes,
        'leg_times' : leg_times
    }
    return ret


def summarize_profile_non_transit_leg (leg, leg_modes, leg_times) :
    if len(leg) == 1:
        leg_modes.append(leg[0]['mode'])
        leg_times.append(leg[0]['time'])
    else:
        modes = []
        times = []
        for mode_option in leg:
            modes.append(mode_option['mode'])
            times.append(mode_option['time'])
        leg_modes.append(modes)
        leg_times.append(times)

# Generate a callback closure containing the unfinished row.
# We could potentially avoid this by only saving the URL or query parameters, and not passing in a row.
def response_callback_factory(row, profile) :
    def handle_response(response, *args, **kwargs) :
        global n # avoid "referenced before assignment" weirdness
        n += 1
        t = (time.time() - t0) / 60.0
        T = (N * t) / n
        print "Request %d/%d, time %0.2f min of %0.2f (estimated) received" % (n, N, t, T), response,
        n_itin = 0
        elapsed = 0
        if response.status_code != 200 :
            status = 'failed'
        else :
            row['itins'] = []
            objs = response.json()
            if profile:
                row['query_type'] = 'profile'
                if 'options' in objs:
                    options = objs['options']
                    n_itin = len(options)
                    # check response for timeout flag
                    status = 'complete'
                    # status = 'timed out'
                else:
                    status = 'no paths'
            else:
                row['query_type'] = 'plan'
                row['debug'] = objs['debugOutput']
                elapsed = objs['debugOutput']['totalTime']
                if 'plan' in objs:
                    itineraries = objs['plan']['itineraries']
                    n_itin = len(itineraries)
                    # check response for timeout flag
                    status = 'complete'
                    # status = 'timed out'
                else:
                    status = 'no paths'
                row['total_time'] = str(elapsed) + ' msec'
                row['avg_time'] = None if n_itin == 0 else '%f msec' % (float(elapsed) / n_itin)

        print status
        response_id = len(response_json) # not threadsafe -- not atomic with following line
        response_json.append( row )
        row['status'] = response.status_code
        row['response_id'] = response_id

        # Create a row for each itinerary/option within this single trip planner result
        if profile:
            for (option_number, option) in enumerate(options) :
                option_row = summarize_profile (option)
                option_row['itinerary_number'] = option_number + 1
                full_itin = {'response_id':response_id,'itinerary_number':option_number+1}
                full_itin['body']=option
                full_itins_json.append( full_itin )
                row['itins'].append( option_row )
        else:
            for (itinerary_number, itinerary) in enumerate(itineraries) :
                itin_row = summarize_plan (itinerary)
                #itin_row['response_id'] = response_id
                itin_row['itinerary_number'] = itinerary_number + 1
                full_itin = {'response_id':response_id,'itinerary_number':itinerary_number+1}
                full_itin['body']=itinerary
                full_itins_json.append( full_itin )
                row['itins'].append( itin_row )

        if SHOW_RESPONSE :
            pp.pprint(row)
    # return the function definition, a closure for a specific instance of 'row'
    return handle_response


def run(connect_args) :
    "This is the principal function..."
    notes = connect_args.pop('notes')
    retry = connect_args.pop('retry')
    fast  = connect_args.pop('fast')
    host = connect_args.pop('host')
    profile = connect_args.pop('profile')
    print("profile=%s"%profile)
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
    global t0, N # HACK
    t0 = time.time()
    N = len(all_params)
    reqs = []
    for params in all_params :
        params = dict(params) # TODO necessary?
        request_id = params.pop('id')
        oid = params.pop('oid')
        tid = params.pop('tid')

        params['date'] = DATE
        if profile:
            api_method = 'profile'
            params['from'] = params.pop('fromPlace')
            params['to'] = params.pop('toPlace')
            params['modes'] = params.pop('mode')
            params['limit'] = 3
        else:
            api_method = 'plan'
            params['numItineraries'] = 3

        qstring = urllib.urlencode(params)
        url = "http://%s/otp/routers/default/%s?%s"%(host, api_method, qstring)

        # Tomcat server + spaces in URLs -> HTTP 505 confusion
        if SHOW_PARAMS :
            pp.pprint(params)
        if SHOW_URL :
            print url
        row = { 'url' : url,
                'run_id' : run_time_id,
                'request_id' : request_id,
                'origin_id' : oid,
                'target_id' : tid,
                'id_tuple' : "%s-%s-%s"%(oid,tid,request_id),
                'membytes' : None }
        # You can't give arguments to the response callback, you have to make a factory function:
        # "http://stackoverflow.com/questions/25115151/how-to-pass-parameters-to-hooks-in-python-grequests"
        # Closures are created in Python by function calls.
        response_callback = response_callback_factory(row, profile)
        headers = {'Accept': 'application/json'}
        req = grequests.get(url, headers=headers, hooks=dict(response=response_callback))
        reqs.append(req)

    # Set max number of concurrent requests to 20, OTP should throttle this via worker threads
    grequests.map(reqs, size=20)

    # Write out all results at the end. Really, this should probably be done in streaming fashion.
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
    parser.add_argument('-p', '--profile', action='store_true', default=False)
    args = parser.parse_args()

    # args is a non-iterable, non-mapping Namespace (allowing usage in the form args.name),
    # so convert it to a dict before passing it into the run function.
    run(vars(args))


