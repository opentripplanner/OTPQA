OTPProfiler
===========

Keep track of changes in OTP performace

Generate random points with: 

    $ python gen_points.py pbf_filename num_points

Generate a bunch of requests with: 

    $ python gen_requests.py 

It takes no arguments, assumes the presence of endpoints_random.py and endpoints_custom.py in the same directory.

Then run the profiler with 

    $ python otpprofiler.py hostname
    
That will generate run_summary.TIMESTAMP.json and full_itins.TIMESTAMP.json
That one can do with what one pleases.