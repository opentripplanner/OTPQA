import simplejson as json
import numpy as np

def parsetime(aa):
	if aa is None:
		return None

	return float( aa.split()[0] )

def main(filenames):
	if len(filenames)==0:
		return

	datasets = []
	for fn in filenames:
		blob = json.load( open(fn) )
		dataset = dict( [(response["id_tuple"], response) for response in blob['responses']] )
		datasets.append( dataset )

	id_tuples = datasets[0].keys()

        if len(id_tuples)==0:
                print "Input does not contain any data"
                exit()

	yield "<html>"
	yield """<head><style>table, th, td {
    border: 1px solid black;
    border-collapse: collapse;
}
th, td {
    text-align: left;
}</style></head>"""

	yield """<table border="1">"""

	dataset_total_times = dict(zip( range(len(datasets)),[[] for x in range(len(datasets))]) )
	dataset_avg_times = dict(zip(range(len(datasets)),[[] for x in range(len(datasets))]) )
	dataset_fails = dict(zip(range(len(datasets)), [0]*len(datasets)))

	for id_tuple in id_tuples:
		yield """<tr><td rowspan="2"><a href="%s">%s</a></td>"""%(datasets[0][id_tuple]['url'], id_tuple)
		for i, dataset in enumerate( datasets ):
			response = dataset[id_tuple]

			dataset_total_times[i].append( parsetime( response['total_time'] ) )
			dataset_avg_times[i].append( parsetime( response['avg_time'] ) )

			yield "<td>%s total, %s avg</td>"%(response['total_time'],response['avg_time'])
		yield "</tr>"

		for i, dataset in enumerate( datasets ):
			yield "<td>"

			response = dataset[id_tuple]

			yield "<table border=1 width=100%><tr>"

			if len(response['itins']) == 0:
				dataset_fails[i] += 1
				yield "<td style=\"background-color:#EDA1A1\">NONE</td>"

			for itin in response['itins']:
				filling = itin['routes']
				if filling=="{}":
					color = "#EDECA1"
				else:
					color = "#AEEDA1"
				yield "<td style=\"background-color:%s\">%s</td>"%(color,filling)

			yield "</tr></table>"
			yield "</td>"
		yield "</tr>"

	yield "<tr><td>stats</td>"
	for i in range(len(datasets)):
		yield "<td>fails: %s (%.2f%%). total time: median:%.2fs mean:%.2fs</td>"%(dataset_fails[i], 100*dataset_fails[i]/float(len(id_tuples)), np.median(dataset_total_times[i]),np.mean(dataset_total_times[i]))
	yield "</tr>"


	yield "</table>"

	yield "</html>"

if __name__=='__main__':
	import sys

	if len(sys.argv)<2:
		print "usage: cmd fn1 [fn2 [fn3 ...]]"
		exit()

	for line in main(sys.argv[1:]):
		print line
