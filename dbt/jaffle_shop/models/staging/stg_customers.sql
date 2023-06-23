with source as (

    {#-
    Normally we would select from the table here, but we are using seeds to load
    our data in this project
    #}
    -- select * from {{ ref('raw_customers_tb') }}
    select * from {{ source('jaffle_shop', 'raw_customers_tb') }}

),

renamed as (

    select
        id as customer_id,
        first_name,
        last_name

    from source

)

select * from renamed
