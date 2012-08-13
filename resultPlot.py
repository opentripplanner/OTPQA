#!/usr/bin/python

import psycopg2, psycopg2.extras, violin

# depends on peer authentication
try:
    conn = psycopg2.connect("dbname='otpprofiler'")
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
except:
    print "Unable to connect to the database. Exiting."
    exit(-1)
    
cur.execute("SELECT * FROM runs ORDER BY run_began DESC LIMIT 4")
runs = cur.fetchall()
run_ids = [run['run_id'] for run in runs] 
labels = [run['git_sha1'][:8] for run in runs]
data = []
# AND avg_time > '1 second'::interval
for run_id in run_ids :
    cur.execute("""SELECT avg_time FROM responses, requests 
        WHERE responses.request_id = requests.request_id
        AND run_id = %s
        AND avg_time IS NOT NULL
        AND requests.mode LIKE '%%,TRANSIT'; """, (run_id,) )
    times = [row[0].total_seconds() for row in cur] # convert datetime.timedelta to fractional seconds
    data.append(times)

violin.violin_plot(data, bp=True, scale=True, labels=labels)

