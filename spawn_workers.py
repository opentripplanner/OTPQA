#!/usr/bin/python
# simple script to request a bunch of AWS spot instances, all of which will run profiler and
# report their results to the same database server.

# make sure you have a .boto in ~/
# containing your AWS API key and secret
import argparse, boto

parser = argparse.ArgumentParser(description='request (multiple) spot instances running as OTPProfiler workers')
parser.add_argument('dbpwd') 
parser.add_argument('dbhost') # internal AWS IP for postgres server
parser.add_argument('--imageid', default='ami-35b0005c')
parser.add_argument('--nworkers', type=int, default=1)

args = parser.parse_args() 

script = """#!/bin/bash
cd /home/ubuntu/git/OTPProfiler
su ubuntu -c 'git pull'
su ubuntu -c './otpprofiler.py %s -p %s --retry 200 > /home/ubuntu/profiler.out &'
""" % (args.dbhost, args.dbpwd)

ec2 = boto.connect_ec2()
reqs = ec2.request_spot_instances('.320', image_id=args.imageid, count=args.nworkers, 
    instance_type='m1.large', key_name='abyrd', security_groups=['default'], user_data=script)

# this returns $count SpotInstanceRequest objects. These do not get updated as progress occurs. 
# Each of these has a unique Spot Instance Request ID.  
# Later, you can do ec2.get_all_spot_instance_requests(), then filter on the Spot Instance Request IDs 
# to find out the status of each request.If the request has been fulfilled, the instance_id attribute 
# of the SpotInstanceRequest object will contain the instance id of the newly created instance.
# however, since the actions to perform on startup have been provided through the user_data script,
# you can simply follow progress on the console.
