--
-- SQL Script for creating (Postgres) tables for OTPProfiler
--

-- Table: runs
CREATE TABLE runs (
    run_id serial PRIMARY KEY NOT NULL,
    git_sha1 character(40) NOT NULL,
    run_began timestamp with time zone NOT NULL,
    run_ended timestamp with time zone NOT NULL,
    git_describe text NOT NULL,
    automated boolean DEFAULT false NOT NULL
);
COMMENT ON TABLE runs IS 'information about individual runs of the profiler, which are usually triggered by git commits via the continuous integration server';
COMMENT ON COLUMN runs.automated IS 'indicates whether the run was automatically started by the continuous integration server';


-- Table: endpoints
CREATE TABLE endpoints (
    endpoint_id serial PRIMARY KEY NOT NULL,
    random boolean NOT NULL,
    lon float NOT NULL,
    lat float NOT NULL,
    name text NOT NULL DEFAULT 'unspecified',
    notes varchar -- can be NULL
);
COMMENT ON TABLE endpoints IS 'origin or destination points for profiling queries';
COMMENT ON COLUMN endpoints.random IS 'whether or not the endpoint was generated as a random batch';
COMMENT ON COLUMN endpoints.location IS 'the (lon,lat) of the endpoint';
COMMENT ON COLUMN endpoints.name IS 'a human-readable name for endpoints, especially those manually entered rather than randomly generated';
COMMENT ON COLUMN endpoints.notes IS 'optional additional information about this endpoint';


-- Table: requests
CREATE TABLE requests (
    request_id serial PRIMARY KEY NOT NULL,
    time time without time zone NOT NULL,
    maxWalkDistance integer NOT NULL,
    modes text NOT NULL,
    min text NOT NULL,
    arriveBy boolean NOT NULL,
    UNIQUE (time, maxWalkDistance, modes, min, arriveBy)
);
COMMENT ON TABLE requests IS 'query parameters used to reproducibly build requests for all origin and destination points';


-- Table: results
CREATE TABLE results (
    result_id serial PRIMARY KEY NOT NULL,
    run_id integer NOT NULL REFERENCES runs,
    request_id integer NOT NULL REFERENCES requests,
    origin_id integer NOT NULL REFERENCES endpoints (endpoint_id),
    target_id integer NOT NULL REFERENCES endpoints (endpoint_id),
    UNIQUE (run_id, request_id, origin_id, target_id),
    response_time interval NOT NULL, 
    membytes integer NOT NULL
);
COMMENT ON TABLE results IS 'summary information about the responses received from the trip planning API during profiling';


-- Table: itineraries
CREATE TABLE itineraries (
    result_id integer NOT NULL REFERENCES results,
    itinerary_number smallint NOT NULL,
    PRIMARY KEY (result_id, itinerary_number),
    -- we could go yet another level and add a legs table, but let's forgo that for now.
    n_legs smallint,
    n_vehicles smallint,
    walk_distance integer,
    wait_time_sec integer,
    ride_time_sec integer,
    start_time timestamp with time zone,
    duration interval
);
COMMENT ON TABLE itineraries IS 'information about the individual itineraries that make up a trip planner response';


