import json

def parsetime(aa):
	if aa is None:
		return None

	return float( aa.split()[0] )

def main(fn1, fn2):
	print fn1, fn2

	data1 = json.load( open(fn1) )
	data2 = json.load( open(fn2) )
	r1_total_time = [ x for x in [parsetime( item["avg_time"] ) for item in data1["responses"]] if x]
	r2_total_time = [ x for x in [parsetime( item["avg_time"] ) for item in data2["responses"]] if x]

	r1_avg = sum(r1_total_time)/len(r1_total_time)
	r2_avg = sum(r2_total_time)/len(r2_total_time)

	print "mean avg_time"
	print "1: %.4fs"%r1_avg
	print "2: %.4fs"%r2_avg
	print "1->2 diff: %.3f%%"%((r2_avg/r1_avg)*100)

if __name__=='__main__':
	import sys

	if len(sys.argv)<3:
		print "usage: cmd filename1 filename2"
		exit()

	fn1 = sys.argv[1]
	fn2 = sys.argv[2]

	main(fn1,fn2)