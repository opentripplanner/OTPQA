from imposm.parser import OSMParser
from random import random, randint, choice

def get_random_points( filename, nn ):

	all_nds = set()
	intersection_nds = set()
	def road(ways):
		for id, tags, nds in ways:
			if 'highway' not in tags:
				continue

			# if we've ever seen any of these nds before, they're intersections	
			for nd in nds:
				if nd in all_nds:
					intersection_nds.add( nd )
				all_nds.add( nd )

	print "collecting intersection nodes..."
	p = OSMParser(concurrency=4, ways_callback=road)
	p.parse(fn)
	intersection_nds = list(intersection_nds)
	print "done"


	print "grab several at random"
	nds = set()
	for i in range(nn):
		nd = choice(intersection_nds)
		while nd in nds:
			nd = choice(intersection_nds)

		nds.add( nd )
	ret = []

	def get_coords(coords):
		for id,lon,lat in coords:

			if id in nds:
				ret.append( (lon,lat) )
				print (lon,lat)

	print "get lat/lon coords of nodes..."
	p = OSMParser(concurrency=1, coords_callback=get_coords)
	p.parse(fn)
	print "done"

	return ret

if __name__=='__main__':
	import sys
	# fn = "/Users/brandon/Documents/nysdot/graph/tristate.pbf"

	if len(sys.argv)<3:
		print "usage: cmd pbf_filename num_points"
		exit()

	fn = sys.argv[1]
	ct = int(sys.argv[2])

	nodes = get_random_points(fn, ct)

	fpout = open("endpoints_random.csv","w")
	fpout.write("name,lat,lon\n")
	for i,(lon,lat) in enumerate(nodes):
		fpout.write("%s,%s,%s\n"%(i,lat,lon))
	fpout.close()

