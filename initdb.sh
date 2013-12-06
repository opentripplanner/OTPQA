#!/bin/bash
echo Dropping db...
sudo -u postgres dropdb otpprofiler
echo Creating db...
sudo -u postgres createdb -O otpprofiler otpprofiler
echo Applying schema...
psql -d otpprofiler -f ./schema.sql
# endpoints should be generated once and stored with baseline graph inputs
# java -Xmx6G -cp ../OpenTripPlanner/opentripplanner-graph-builder/target/graph-builder.jar \
#     org.opentripplanner.graph_builder.GraphStats \
#     --graph /var/otp/graphs/pdx_baseline/Graph.obj \
#     -o endpoints_random.csv endpoints -n 50 -s --radius 2000 
echo Populating request parameters and endpoints tables...
python ./populate_db.py

