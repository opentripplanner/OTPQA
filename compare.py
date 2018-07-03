import simplejson as json

UNRESTRICTED_MODES = set(["WALK", "BICYCLE", "CAR"])

def parsetime(aa):
	if aa is None:
		return None

	return float( aa.split()[0] )

def extractdurations(filename):
        blob = json.load( open(filename) )
        dataset = dict( [(response["id_tuple"], response) for response in blob["responses"]] )

        durations = {}

        for id_tuple in dataset:
                response = dataset[id_tuple]

                if not "itins" in response or len(response["itins"]) == 0:
                        durations[id_tuple] = -1
                else:
			durations[id_tuple] = parsetime( response["itins"][0]["duration"] )
        return durations

def extractitineraries(filename):
        blob = json.load( open(filename) )
        dataset = dict( [(response["id_tuple"], response) for response in blob["responses"]] )

        itineraries = {}

        for id_tuple in dataset:
                response = dataset[id_tuple]

                if not "itins" in response:
                        itineraries[id_tuple] = 0
                else:
			itineraries[id_tuple] = len(response["itins"])
        return itineraries

def extractmodes(filename):
        blob = json.load( open(filename) )
        dataset = dict( [(response["id_tuple"], response) for response in blob["responses"]] )

        num_modes = {}

        for id_tuple in dataset:
                response = dataset[id_tuple]

                if not "itins" in response or len(response["itins"]) == 0:
                        num_modes[id_tuple] = 0
                else:
                        modes_set = set()
                        for itinerary in response["itins"]:
                                if len(set(itinerary).difference(UNRESTRICTED_MODES)) == 0:
                                        modes_set.union(itinerary["leg_modes"])
                                else:
                                        #Do not include WALK, BICYCLE or CAR if there are other modes
                                        modes_set.union(set(itinerary["leg_modes"]).difference(UNRESTRICTED_MODES))
			        modes_set.union(itinerary["leg_modes"])
                        num_modes[id_tuple] = len(modes_set)
        return num_modes

def main(args):
        fname1 = args.pop('benchmark')
        fname2 = args.pop('profile')
        threshold = args.pop('threshold')
        limit = args.pop('limit')
        itineraries = args.pop('itineraries')
        itinerary_threshold = args.pop('itinerarythreshold')
        modes = args.pop('modes')
        mode_threshold = args.pop('modethreshold')

        print "Detecting regressions with a time threshold of %d seconds and test threshold %d "%(threshold, limit)

        dur1 = extractdurations(fname1)
        dur2 = extractdurations(fname2)

        itin1 = {}
        itin2 = {}

        if itineraries:
                print "Detecting regressions with a itinerary number threshold of %d and test threshold %d "%(itinerary_threshold, limit)
                itin1 = extractitineraries(fname1)
                itin2 = extractitineraries(fname2)

        modes1 = {}
        modes2 = {}

        if modes:
                print "Detecting regressions with a mode number threshold of %d and test threshold %d "%(mode_threshold, limit)
                modes1 = extractmodes(fname1)
                modes2 = extractmodes(fname2)

        fails1 = 0
        fails2 = 0
        slower1 = 0
        slower2 = 0
        count = 0

        less_itin1 = 0
        less_itin2 = 0

        less_mode1 = 0
        less_mode2 = 0

	for id in dur1:
                if not id in dur2:
                        print "test data is not comparable"
                        exit(1)
                t1 = dur1[id]
                t2 = dur2[id]
                if t1 != t2:
                        diffmsg = "Test route duration %s t1=%d t2=%d diff=%d"%(id, t1, t2, t2-t1)
                        if t1 < 0 and t2 > 0:
                                fails1+=1
                        elif t1 > 0 and t2 < 0:
                                fails2+=1
                        elif t1 > t2 + threshold:
                                slower1+=1
                        elif t2 > t1 + threshold:
                                slower2+=1
                        else:
                                diffmsg = ""

                        if diffmsg:
                                print diffmsg

                if itineraries:
                        i1 = itin1[id]
                        i2 = itin2[id]

                        if i1 != i2:
                                diffmsg = "Test itinerarys %s t1=%d t2=%d diff=%d"%(id, i1, i2, i2-i1)
                                if i2 >= i1 + itinerary_threshold:
                                        less_itin1+=1
                                elif i1 >= i2 + itinerary_threshold:
                                        less_itin2+=1
                                else:
                                        diffmsg = ""

                                if diffmsg:
                                        print diffmsg

                if modes:
                        m1 = modes1[id]
                        m2 = modes2[id]

                        if i1 != i2:
                                diffmsg = "Test modes %s t1=%d t2=%d diff=%d"%(id, m1, m2, m2-m1)
                                if m2 >= m1 + itinerary_threshold:
                                        less_mode1+=1
                                elif m1 >= m2 + itinerary_threshold:
                                        less_mode2+=1
                                else:
                                        diffmsg = ""

                                if diffmsg:
                                        print diffmsg

                count+=1

        print "Test count: %d"%count
        print "Routings that failed only in %s: %d"%(fname1, fails1)
        print "Routings that failed only in %s: %d"%(fname2, fails2)
        print "Routes that are slower in %s: %d"%(fname1, slower1)
        print "Routes that are slower in %s: %d"%(fname2, slower2)

        print "Route duration regressions: %d"%(fails2 + slower2)
        rate = int(100*float(count + fails1 - fails2 + slower1 - slower2)/float(count))
        print "Route duration comparison rate: %d"%rate
        fail = False
        if rate < limit:
                print "Route duration test failed, %d < %d"%(rate, limit)
                fail = True
        if itineraries:
                print "Routes that have less itineraries in %s: %d"%(fname1, less_itin1)
                print "Routes that have less itineraries in %s: %d"%(fname2, less_itin2)
                rate = int(100*float(count + less_itin1 - less_itin2)/float(count))
                if rate < limit:
                        print "Itinerary test failed, %d < %d"%(rate, limit)
                        fail = True
        if modes:
                print "Routes that have less modes in %s: %d"%(fname1, less_mode1)
                print "Routes that have less modes in %s: %d"%(fname2, less_mode2)
                rate = int(100*float(count + less_mode1 - less_mode2)/float(count))
                if rate < limit:
                        print "Mode test failed, %d < %d"%(rate, limit)
                        fail = True
        if fail:
                exit(1)
        print "Test passed"

if __name__=="__main__":
	import sys
        import argparse

        parser = argparse.ArgumentParser(description='Compare two routing profiles to detect slower routes and failed routing requests')
        parser.add_argument('benchmark')
        parser.add_argument('profile')
        parser.add_argument('-t', '--threshold', type=int, default=60) #seconds. Route duration changes less than this are ignored
        parser.add_argument('-l', '--limit', type=int, default=95) #failure limit percentage. If share of equally good routes is below this, exit with nonzero code.
        parser.add_argument('-i', '--itineraries', action='store_true', default=False) #compare number of itineraries
        parser.add_argument('-it', '--itinerarythreshold', type=int, default=1) #Changes in number of itineraries less than this are ignored
        parser.add_argument('-m', '--modes', action='store_true', default=False) #compare mode variation in itineraries
        parser.add_argument('-mt', '--modethreshold', type=int, default=1) #Changes in number of modes less than this are ignored

        args = parser.parse_args()
        main(vars(args))
