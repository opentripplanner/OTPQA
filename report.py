import json
import numpy as np

def parsetime(aa):
	if aa is None:
		return None

	return float( aa.split()[0] )

def itins_ridetime_tuple(resp):
	ret = []

	for itin in resp['itins']:
		ret.append( int(itin['ride_time_sec']) )

	return tuple(ret)

def main(filenames):

	datasets = [ json.load( open(fn) ) for fn in filenames ]

	total_times = []
	for dataset in datasets:
		total_time = [ x for x in [parsetime( item["avg_time"] ) for item in dataset["responses"]] if x]
		total_times.append( total_time )

	print "n\tmean(avg_time)\tmedian(avg_time)"
	for i, total_time in enumerate( total_times ):
		time_avg = sum(total_time)/len(total_time)
		time_median = np.median( total_time )
		print "%d\t%0.4f\t%0.4f"%(i, time_avg,time_median)


	# collate responses in every dataset by (origin_id,target_id,request_id) tuple
	ff = {}
	for i, dataset in enumerate( datasets ):
		for resp in dataset['responses']:
			req_id = (resp['origin_id'], resp['target_id'], resp['request_id'])
			if req_id not in ff:
				ff[req_id] = {}
			ff[req_id][i] = resp

	for key in ff:
		responses = ff[key]
		if len(responses)==0:
			continue
		print responses[0]['url']

		print key,
		print "\t",
		for i in range(len(datasets)):
			print responses[i]['avg_time'],
			print "\t",
			print itins_ridetime_tuple(responses[i]),
			print "\t",
		print

if __name__=='__main__':
	import sys

	if len(sys.argv)<2:
		print "usage: cmd fn1 [fn2 [fn3 ...]]"
		exit()

	main(sys.argv[1:])