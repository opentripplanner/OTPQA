#!/usr/bin/python
# simple script to request a bunch of AWS spot instances, all of which will run profiler and
# report their results to the same database server.

# make sure you have a .boto in ~/
# containing your AWS API key and secret
import argparse, boto

parser = argparse.ArgumentParser(description='request (multiple) spot instances running as OTPProfiler workers')
parser.add_argument('dbpwd') 
parser.add_argument('--dbhost', default='10.120.178.91') # internal AWS IP
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

