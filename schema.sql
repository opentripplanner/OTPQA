--
-- SQL Script for creating (Postgres) tables for OTPProfiler
--

-- Table: runs
CREATE TABLE runs (
    run_id serial PRIMARY KEY NOT NULL,
    git_sha1 character(40) NOT NULL,
    git_describe text, -- will be null for runs before the first tag is made on the repo
    run_began timestamp with time zone NOT NULL,
    run_ended timestamp with time zone, -- will be null until run completes
    automated boolean DEFAULT false NOT NULL,
    username text,
    notes text -- may be null    
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
COMMENT ON COLUMN endpoints.name IS 'a human-readable name for endpoints, especially those manually entered rather than randomly generated';
COMMENT ON COLUMN endpoints.notes IS 'optional additional information about this endpoint';


-- Table: requests
CREATE TABLE requests (
    -- NOTE the use of double quotes to force case-sensitivity for column names. 
    -- These columns represent query parameters that will be substituted directly into URLs,
    -- and URLs are defined to be case-sensitive.  
    request_id serial PRIMARY KEY NOT NULL,
    time time without time zone NOT NULL,
    "maxWalkDistance" integer NOT NULL,
    mode text NOT NULL,
    min text NOT NULL,
    "arriveBy" boolean NOT NULL,
    typical boolean NOT NULL,
    UNIQUE (time, "maxWalkDistance", mode, min, "arriveBy")
);
COMMENT ON TABLE requests IS 'query parameters used to reproducibly build requests for all origin and destination points';


-- Table: responses
CREATE TYPE response_status AS ENUM ('complete', 'timed out', 'failed', 'no paths');
CREATE TABLE responses (
    -- replace surrogate key with composite key?
    response_id serial PRIMARY KEY NOT NULL,
    run_id integer NOT NULL REFERENCES runs,
    request_id integer NOT NULL REFERENCES requests,
    origin_id integer NOT NULL REFERENCES endpoints (endpoint_id),
    target_id integer NOT NULL REFERENCES endpoints (endpoint_id),
    UNIQUE (run_id, response_id, origin_id, target_id),
    status response_status NOT NULL,
    total_time interval NOT NULL, 
    avg_time interval, -- per itinerary, redundant but useful. NULL when there are 0 itineraries
    membytes integer
);
COMMENT ON TABLE responses IS 'summary information about the responses received from the trip planning API during profiling';


-- Table: itineraries
CREATE TABLE itineraries (
    response_id integer NOT NULL REFERENCES responses,
    itinerary_number smallint NOT NULL,
    PRIMARY KEY (response_id, itinerary_number),
    start_time timestamp with time zone NOT NULL,
    duration interval NOT NULL,
    n_legs smallint,
    n_vehicles smallint,
    walk_distance integer,
    wait_time_sec integer,
    ride_time_sec integer,
    -- we could add a legs table or a composite type, but let's forgo that and use arrays for now.
    routes text[],
    trips text[],
    waits integer[]
);
COMMENT ON TABLE itineraries IS 'information about the individual itineraries that make up a trip planner response';


