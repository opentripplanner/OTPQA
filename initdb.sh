#!/bin/sh
echo Dropping db...
sudo -u postgres dropdb otpprofiler
echo Creating db...
sudo -u postgres createdb -O $USER otpprofiler
echo Applying schema...
psql -d otpprofiler -f ./schema.sql
# endpoints should be generated once and stored with baseline graph inputs
# java -Xmx6G -cp OTP_PATH/otp.jar \
#     org.opentripplanner.graph_builder.GraphStats \
#     --graph GRAPH_PATH/Graph.obj \
#     -o endpoints_random.csv endpoints -n 50 -s --radius 2000 
echo Populating request parameters and endpoints tables...
python ./populate_db.py
