-- Boogle table schemas
-- TODO: Fill in schema and entries as needed! 

CREATE TABLE IF NOT EXISTS clients (
    client_id   UUID PRIMARY KEY,
    first_seen  TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS requests (
    request_id  BIGSERIAL PRIMARY KEY,
    client_id   UUID REFERENCES clients(client_id),
    ts          TIMESTAMPTZ NOT NULL DEFAULT now(),
    ip          INET,
    referer     TEXT,
    path        TEXT
);

CREATE TABLE IF NOT EXISTS searches (
    search_id   BIGSERIAL PRIMARY KEY,
    client_id   UUID REFERENCES clients(client_id),
    request_id  BIGINT REFERENCES requests(request_id),
    query       TEXT NOT NULL,
    ts          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create indices for faster reverse order lookups 
CREATE INDEX IF NOT EXISTS searches_by_client ON searches (client_id, ts DESC, search_id DESC);
CREATE INDEX IF NOT EXISTS requests_by_client ON requests (client_id, ts DESC, request_id DESC);

-- Create function to aggregate and format searches for a client_id
CREATE OR REPLACE FUNCTION boogleschema.get_searches_by_id (user_id UUID)
RETURNS json 
LANGUAGE sql
STABLE
AS $function$
-- create object {} with entry 'searches'
SELECT COALESCE (
    -- coalesce into empty [] if no searches
    json_agg(
        -- format each search with entries 'query' and 'ts'
        json_build_object(
            'query', s.query,
            'ts', to_char(
                -- format time stamp
                s.ts AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'
            )
        )
        -- order reverse chronological with search_id as tiebreaker
        ORDER BY s.ts DESC, s.search_id DESC
    ), '[]'::json
) 
FROM searches s
WHERE s.client_id = user_id;
$function$;

-- ********************************************* --

-- Create function to aggregate and format dump data from all clients
CREATE OR REPLACE FUNCTION boogleschema.dump_data()
RETURNS json 
LANGUAGE sql
STABLE
AS $function$
-- create dump object {}
SELECT json_build_object(
    -- coalesce in case of no clients
    'clients', COALESCE (
        -- aggregate all clients into 'clients' array []
        json_agg(
            -- create object for individual client
            json_build_object(
                'client_id', c.client_id,
                'first_seen', to_char(
                    c.first_seen AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'
                ), 
                'last_seen', to_char(
                    c.last_seen AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'
                ), 
                'latest_ip', boogleschema.get_latest_ip(c.client_id),
                'ips', boogleschema.get_client_ips(c.client_id),
                'searches', boogleschema.get_searches_by_id(c.client_id)
            )
        ), '[]'::json
    )
) 
FROM clients c;
$function$;

-- ********************************************* --

-- create function to get ips for a given client_id from requests
CREATE OR REPLACE FUNCTION boogleschema.get_client_ips(user_id UUID)
RETURNS json 
LANGUAGE sql
STABLE
AS $function$
    SELECT COALESCE (
		json_agg (
	        DISTINCT r.ip
		), '[]'::json 
    )
    FROM requests r
    WHERE r.client_id = user_id; -- match to user_id
$function$;

-- ********************************************* --

-- create function to get lastest ip given a client_id from requests
CREATE OR REPLACE FUNCTION boogleschema.get_latest_ip(user_id UUID)
RETURNS INET 
LANGUAGE sql
STABLE
AS $function$
    SELECT r.ip -- select ip
    FROM requests r
    WHERE r.client_id = user_id -- match to user_id
    ORDER BY r.ts DESC -- order requests by timestamp descending
    LIMIT 1;
$function$;