with races as (

    select * from {{ ref('stg_races_result') }}

),


final as (

    select "driver_id",  
            sum("points") as "total_points" 
            
    from races

    group by "driver_id"

    order by "total_points" desc 

)


select * from final