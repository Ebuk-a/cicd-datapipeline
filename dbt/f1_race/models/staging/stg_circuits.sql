with source as (

    {#-
    Normally we would select from the table here, but we are using seeds to load
    our data in this project
    #}
    select * from {{ source('postgres_public_dw', 'raw_circuits') }}
    

),

renamed as (

    select
        "circuit_id", 
        "url", 
        "circuit_name", 
        "location_lat" as "latitude",
        "location_long" as "longtitude",
        "location_locality" as "locality",
        "location_country" as "country", 
        "_etl_loaded_at"

    from source

)

select * from renamed
