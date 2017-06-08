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

def main(filenames):
        dur1 = extractdurations(filenames[0])
        dur2 = extractdurations(filenames[1])

        fails1 = 0
        fails2 = 0
        slower1 = 0
        slower2 = 0
        count = 0

	for id in dur1:
                if not id in dur2:
                        print "test data is not comparable"
                        exit()
                t1 = dur1[id]
                t2 = dur2[id]
                if t1 != t2:
                        print "Test %s t1=%d t2=%d"%(id, t1, t2)
                if t1 < 0 and t2 > 0:
                        fails1+=1
                elif t1 > 0 and t2 < 0:
                        fails2+=1
                elif t1 > t2:
                        slower1+=1
                elif t1 < t2:
                        slower2+=1
                count+=1


        print "Test count: %d"%count
        print "Routings that failed only in %s: %d"%(filenames[0], fails1)
        print "Routings that failed only in %s: %d"%(filenames[1], fails2)
        print "Routes that are slower in %s: %d"%(filenames[0], slower1)
        print "Routes that are slower in %s: %d"%(filenames[1], slower2)

        print "Regressions: %d"%(fails2 + slower2)
        print "Comparison rate:"
        print (float(count + fails1 - fails2 + slower1 - slower2)/float(count))

if __name__=="__main__":
	import sys

	if len(sys.argv)!=3:
		print "usage: cmd fn1 fn2]"
		exit()
	main(sys.argv[1:])

