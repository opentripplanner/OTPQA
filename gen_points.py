from imposm.parser import OSMParser
from random import random, randint, choice
import os
from zipfile import ZipFile
import csv
from pyproj import Geod

MAX_TRIES = 10000

def point_near_points(geod,radius,lon,lat,lons,lats):
	if len(lons)!=len(lats):
		raise Exception( "lons and lats not the same size" )

	x,y,dists = geod.inv([lon]*len(lons), [lat]*len(lons), lons, lats)
	for dist in dists:
		if dist<=radius:
			return True
	return False

def get_random_points( dirname, nn, radius=2000 ):

	filenames = os.listdir( dirname )

	pbfs = [x for x in filenames if x[-7:]=="osm.pbf"]
	if len(pbfs)==0:
		raise Exception( "no pbf file in directory" )
	if len(pbfs)>1:
		raise Exception(" more than one pbf file in directory" )
	pbffilename = os.path.join( dirname, pbfs[0] )

	zip_fns = [x for x in filenames if x[-4:]==".zip"]

	if len(zip_fns)==0:
		raise Exception( "no gtfs feeds in directory" )

	stop_lats = []
	stop_lons = []
	for fn in zip_fns:
		zf = ZipFile( os.path.join( dirname, fn ) )
		try:
			fp = zf.open("stops.txt")
		except KeyError, e:
			continue

		rd = csv.reader(fp)
		header = rd.next()
		try:
			lat_ix = header.index("stop_lat")
			lon_ix = header.index("stop_lon")
		except ValueError, e:
			continue 

		for row in rd:
			stop_lats.append( float(row[lat_ix]) )
			stop_lons.append( float(row[lon_ix]) )

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
	p.parse(pbffilename)
	intersection_nds = list(intersection_nds)
	print "done"

	print "get lat/lon coords of nodes..."
	nd_coords = {}
	def get_coords(coords):
		for id,lon,lat in coords:
			nd_coords[id] = (lon,lat)

	p = OSMParser(concurrency=1, coords_callback=get_coords)
	p.parse(pbffilename)

	print "grab several at random"
	geod = Geod(ellps="WGS84")
	nds = set()
	ret = []

	i = 0
	while len(ret)<nn:
		i+=1
		if i>MAX_TRIES:
			raise Exception("can't find intersections near stops")

		# pick one we haven't picked before
		nd = choice(intersection_nds)
		while nd in nds:
			nd = choice(intersection_nds)

		# check that it's within radius of a stop
		lon,lat = nd_coords[nd]
		if point_near_points( geod, radius, lon,lat, stop_lons,stop_lats ):
			nds.add( nd )
			ret.append( nd_coords[nd] )

	print "done"

	return ret

if __name__=='__main__':
	import sys
	# fn = "/Users/brandon/Documents/nysdot/graph/tristate.pbf"

	if len(sys.argv)<3:
		print "usage: cmd dirname num_points"
		exit()

	dirname = sys.argv[1]
	ct = int(sys.argv[2])

	nodes = get_random_points(dirname, ct)

	fpout = open("endpoints_random.csv","w")
	fpout.write("name,lat,lon\n")
	for i,(lon,lat) in enumerate(nodes):
		fpout.write("%s,%s,%s\n"%(i,lat,lon))
	fpout.close()


