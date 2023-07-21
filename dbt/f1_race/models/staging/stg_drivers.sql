with source as (

    {#-
    Normally we would select from the table here, but we are using seeds to load
    our data in this project
    #}
    select * from {{ source('postgres_public_dw', 'raw_drivers') }}
    

),

renamed as (

    select
        "driver_id", 
        "url", 
        "given_name",
        "family_name", 
        "date_of_birth", 
        "nationality", 
        "permanent_number", 
        "code",
        "_etl_loaded_at"

    from source

)

select * from renamed
