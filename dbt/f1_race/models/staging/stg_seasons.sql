with source as (

    {#-
    Normally we would select from the table here, but we are using seeds to load
    our data in this project
    #}
    select * from {{ source('postgres_public_dw', 'raw_seasons') }}
    

),

renamed as (

    select
        "season", 
        "url",
        "_etl_loaded_at"

    from source

)

select * from renamed
