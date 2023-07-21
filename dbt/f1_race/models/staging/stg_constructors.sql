with source as (
    
    {#-
    Normally we would select from the table here, but we are using seeds to load
    our data in this project
    #}
    select * from {{ source('postgres_public_dw', 'raw_constructors') }}
    

),

renamed as (

    select
        "constructor_id", 
        "url", 
        "name" as "constructor_name", 
        "nationality", 
        "_etl_loaded_at"

    from source

)

select * from renamed
