-- Finds nearest volunteers by joining users, details, and locations.
-- Filters by distance using ST_DWithin for performance.
SELECT
    u.user_id,
    ST_Y(vl.curr_loc::geometry) AS latitude,
    ST_X(vl.curr_loc::geometry) AS longitude,
    ST_Distance(
        vl.curr_loc::geography, -- Use the correct column
        ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
    ) AS distance_in_meters
FROM
    {TABLE_USERS} AS u
JOIN
    {TABLE_VOL_DETAILS} AS vd ON u.user_id = vd.user_id
JOIN
    {TABLE_VOL_LOCATIONS} AS vl ON u.user_id = vl.user_id
WHERE
    -- This is the main search filter
    ST_DWithin(
        vl.curr_loc::geography, -- Use the correct column
        ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
        %s
    )
ORDER BY
    distance_in_meters ASC
LIMIT %s;