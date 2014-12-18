OTPQA
=====

Keep track of changes in OTP performance as development progresses, and catch breaking changes to input data sets by observing changes in routing results.

You will need Python and some Python libraries. For the libraries, on a Debian based system like Ubuntu you can run:

`$ sudo apt-get install python-simplejson python-scipy`

We also use grequests to handle multiple concurrent HTTP requests.

`$ sudo pip install grequests`

Generate random points with: 

    $ python gen_points.py dirname num_points

`dirname` is the name of a directory with OSM and GTFS data.

Generate the request parameters and save the request endpoints with: 

    $ python gen_requests.py 

It takes no arguments, assumes the presence of endpoints_random.csv and endpoints_custom.csv in the same directory.

Then run the profiler with 

    $ python otpprofiler.py hostname
    
That will generate run_summary.TIMESTAMP.json and full_itins.TIMESTAMP.json
That one can do with what one pleases.

To generate a report run

    $ python report.py filename1.json filename2.json

To generate an HTML report, run

    $ python hreport.py f1 [fn2 [fn3 ...]] > report.html

