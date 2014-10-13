#!/usr/bin/env python

from csv import writer
from os.path import basename
from psycopg2 import connect
from sys import argv
from sys import stderr
from sys import stdout

argc = len (argv)

if (argc != 3):
	quit ("Usage: %s original comparison" % basename (argv[0]))

original = argv[1]
comparison = argv[2]

try:
	db = connect ("dbname = otpprofiler")
	cursor = db.cursor ()
except:
	quit ("Unable to connect to the database. Exiting.")

log = writer (stderr)
output = writer (stdout)

cursor.execute("""
	SELECT *
	FROM runs
	WHERE run_id = %s OR run_id = %s;
""", (original, comparison))

result = cursor.fetchall ()
log.writerows (result)

cursor.execute ("""
	CREATE TEMPORARY TABLE results ON COMMIT DROP AS
	SELECT	origin_id, target_id, request_id, run_id,
		array_agg (duration) AS duration_array,
		array_agg (n_legs) AS n_legs_array,
		array_agg (n_vehicles) AS n_vehicles_array
	FROM responses NATURAL LEFT JOIN itineraries
	GROUP BY response_id
	ORDER BY origin_id, target_id, request_id, run_id ASC;
""")

cursor.execute ("""
	SELECT	original.origin_id, original.target_id, original.request_id,
		original.duration_array AS original_duration_array,
		comparison.duration_array AS comparison_duration_array,
		original.n_legs_array AS original_n_legs_array,
		comparison.n_legs_array AS comparison_n_legs_array,
		original.n_vehicles_array AS original_n_vehicles_array,
		comparison.n_vehicles_array AS comparison_n_vehicles_array
	FROM results AS original, results AS comparison
	WHERE	original.origin_id = comparison.origin_id
		AND original.target_id = comparison.target_id
		AND original.request_id = comparison.request_id
		AND	(original.duration_array != comparison.duration_array
			OR original.n_legs_array != comparison.n_legs_array
			OR original.n_vehicles_array != comparison.n_vehicles_array)
		AND original.run_id = %s AND comparison.run_id = %s;
""", (original, comparison))

result = cursor.fetchall ()

for row in result:
	for column in row:
		if column == [None]:
			del column[:]

output.writerows (result)

cursor.close ()
db.close ()
