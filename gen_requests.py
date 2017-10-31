import csv
import json


def generateRequestsFromEndpoints(endpoints,TEST_ALL_MODES=True,random=False):
    json_out = {}

    # Initialize the otpprofiler DB 'requests' table with query parameters.
    # Note that on-street modes are not walk-limited, so we don't want to vary the max walk param there.
    # another way to do this would be to store the various values in tables, and construct this
    # view as a constrained product of all the other tables (probably eliminating the synthetic keys).

    # (time, arriveBy)
    times = [ ("08:50:00", False ),
              ("14:00:00", True ),
              ("18:00:00", False),
              ("23:45:00", True) ]

    if TEST_ALL_MODES:
        # (mode, walk, min)
        modes = [ ("WALK,TRANSIT", 20000, "QUICK") ]
        modes.append( ("BICYCLE,TRANSIT", 40000, "QUICK") )
        modes.append( ("WALK", 20000, "QUICK") )
        modes.append( ("BICYCLE", 20000, "SAFE") )
    else:
        # (mode, walk, min)
        modes = [ ("WALK,TRANSIT", 20000, "QUICK") ]

    all_params = [(time, walk, mode, minimize, arriveBy)
        for (time, arriveBy) in times
        for (mode, walk, minimize) in modes]

    requests_json = []
    for i, params in enumerate( all_params ) :
        # NOTE the use of double quotes to force case-sensitivity for column names. These columns
        # represent query parameters that will be substituted directly into URLs, and URLs are defined
        # to be case-sensitive.

        time,maxWalkDist,mode,min,arriveBy = params
        typical = (time=="08:50:00" and maxWalkDist == 2000 and "BICYCLE" not in mode)

        requests_json.append( dict(zip(('time','maxWalkDistance','mode','min','arriveBy','typical','id'),params+(typical,i))) )
    json_out['requests'] = requests_json

    # Initialize the otpprofiler DB with random endpoints and user-defined endpoints
    import csv
    endpoints_json = []

    for i, rec in enumerate( endpoints ):
        endpoint_rec = {'id':i, 'random':random, 'lon':float(rec['lon']), 'lat':float(rec['lat']), 'name':rec['name'], 'notes':None}
        endpoints_json.append( endpoint_rec )
    json_out['endpoints'] = endpoints_json

    return json_out


if __name__ == '__main__':
    endpoints = open("hsl_places.csv.clustered")
    reader = csv.DictReader(endpoints)

    endpoints = list(reader)

    json_out = generateRequestsFromEndpoints(endpoints)
    fpout = open("requests.json","w")
    json.dump(json_out, fpout, indent=2 )
    fpout.close()
