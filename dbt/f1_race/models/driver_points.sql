with races as (

    select * from {{ ref('stg_races_result') }}

),


final as (

    select "driver_id",  
            sum("points") as "total_pointsss" 
            
    from races

    group by "driver_id"

    order by "total_pointss" desc 

)


select * from final
