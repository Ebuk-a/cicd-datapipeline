with source as (

    {#-
    Normally we would select from the table here, but we are using seeds to load
    our data in this project
    #}
    select * from {{ source('postgres_public_dw', 'raw_schedules') }}
    

),

renamed as (

    select
        "datetime", 
        "season", 
        "round", 
        "url",
        "race_name", 
        "circuit_id", 
        "first_practice_datetime",
        "second_practice_datetime", 
        "third_practice_datetime", 
        "qualifying_datetime",
        "sprint_datetime",
        "_etl_loaded_at"


    from source

)

select * from renamed
