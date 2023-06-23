
-- Use the `ref` function to select from other models

select *
from {{ ref('test_model') }}
where id = 1