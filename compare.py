import simplejson as json

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

def main(args):
        fname1 = args.pop('benchmark')
        fname2 = args.pop('profile')
        threshold = args.pop('threshold')
        limit = args.pop('limit')

        print "Detecting regressions with a time threshold of %d seconds and test threshold %d "%(threshold, limit)

        dur1 = extractdurations(fname1)
        dur2 = extractdurations(fname2)

        fails1 = 0
        fails2 = 0
        slower1 = 0
        slower2 = 0
        count = 0

	for id in dur1:
                if not id in dur2:
                        print "test data is not comparable"
                        exit(1)
                t1 = dur1[id]
                t2 = dur2[id]
                if t1 != t2:
                        diffmsg = "Test %s t1=%d t2=%d diff=%d"%(id, t1, t2, t2-t1)
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

                count+=1

        print "Test count: %d"%count
        print "Routings that failed only in %s: %d"%(fname1, fails1)
        print "Routings that failed only in %s: %d"%(fname2, fails2)
        print "Routes that are slower in %s: %d"%(fname1, slower1)
        print "Routes that are slower in %s: %d"%(fname2, slower2)

        print "Regressions: %d"%(fails2 + slower2)
        rate = int(100*float(count + fails1 - fails2 + slower1 - slower2)/float(count))
        print "Comparison rate: %d"%rate
        if rate < limit:
                print "Test failed, %d < %d"%(rate, limit)
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

        args = parser.parse_args()
        main(vars(args))
