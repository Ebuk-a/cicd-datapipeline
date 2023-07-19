with source as (

    {#-
    Normally we would select from the table here, but we are using seeds to load
    our data in this project
    #}
    select * from {{ source('postgres_public_dw', 'raw_races_result') }}
    

),

renamed as (

    select
        "driver_id", 
        "constructor_id", 
        "race_name", 
        "season", 
        "round",
        "circuit_id", 
        "number", 
        "position", 
        "position_text", 
        "points", 
        "grid", 
        "laps", 
        "status", 
        "time_millis", 
        "time_time", 
        "fastest_lap_rank", 
        "fastest_lap", 
        "fastest_lap_avg_speed", 
        "datetime_utc", 
        "_etl_loaded_at"

    from source

)

select * from renamed
