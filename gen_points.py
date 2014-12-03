from imposm.parser import OSMParser
from random import random, randint, shuffle
import os
from zipfile import ZipFile
import csv
from pyproj import Geod
from scipy.spatial import KDTree
from math import radians, cos

def point_near_points(geod,radius,lon,lat,lons,lats):
	if len(lons)!=len(lats):
		raise Exception( "lons and lats not the same size" )

	x,y,dists = geod.inv([lon]*len(lons), [lat]*len(lons), lons, lats)
	for dist in dists:
		if dist<=radius:
			return True
	return False

def project(coord) :
	"This projection completely wrecks heading but preserves distances. (lon, lat) -> (x, y)"
	m_per_degree = 111111.0
	lon, lat = coord
	y = lat * m_per_degree
	x = lon * cos(radians(lat)) * m_per_degree
	return (x, y)
	
def get_random_points( dirname, nn, radius=2000 ):

	filenames = os.listdir( dirname )

	pbfs = [x for x in filenames if x[-7:]=="osm.pbf"]
	if len(pbfs)==0:
		raise Exception( "no pbf file in directory" )
	if len(pbfs)>1:
		raise Exception(" more than one pbf file in directory" )
	pbffilename = os.path.join( dirname, pbfs[0] )

	zip_filenames = [x for x in filenames if x[-4:]==".zip"]

	if len(zip_filenames)==0:
		raise Exception( "No GTFS feeds found in directory." )

	print "Collecting stop locations from GTFS files..."
	stop_coords = []
	for fn in zip_filenames:
		print "  ", fn
		zf = ZipFile( os.path.join( dirname, fn ) )
		try:
			fp = zf.open("stops.txt")
		except KeyError, e:
			print "This ZIP file does not contain a stops.txt, skipping."
			continue
		rd = csv.reader(fp)
		header = rd.next()
		try:
			lat_idx = header.index("stop_lat")
			lon_idx = header.index("stop_lon")
		except ValueError, e:
			print "Stops.txt does not contain lat or lon columns, skipping."
			continue 
		for row in rd:
			stop_coords.append( (float(row[lon_idx]), float(row[lat_idx])) )
	print "Done."

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

	print "Collecting intersection nodes from PBF file..."
	print "  ", pbffilename
	# concurrency is automatically set to number of cores
	p = OSMParser(ways_callback=road)
	p.parse(pbffilename)
	all_nds.clear() # cannot del() because it's referenced in a nested scope	
	print "Done."

	nd_coords = {}
	def get_coords(coords):
		for id, lon, lat in coords:
			if (id in intersection_nds):
				nd_coords[id] = (lon, lat)

	print "Getting lat/lon coordinates of intersection nodes..."
	p = OSMParser(coords_callback=get_coords)
	p.parse(pbffilename)
	print "Done."

	print "Adding projected GTFS stop locations to a KD tree."
	# kdtree requires a long-lived immutable input, so make a copy
	projected_stop_coords = map(project, stop_coords)
	kdtree = KDTree(projected_stop_coords)
	print "Done."

	print "Choosing nodes near transit at random..."
	geod = Geod(ellps="WGS84")
	ret = []
	intersection_nds = list(intersection_nds)
	shuffle(intersection_nds)
	for nd in intersection_nds :
		# Check that it's within radius of a stop
		coord = nd_coords[nd]
		distance, nearest_coord = kdtree.query(project(coord))
		if distance > radius: 
			continue
		ret.append( coord )
		if len(ret) >= nn: 
			break

	print "Done."
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


