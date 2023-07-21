from airflow.decorators import dag
from cosmos.task_group import DbtTaskGroup
from pendulum import datetime

CONNECTION_ID = "postgres_default"
DB_NAME = "postgres"
SCHEMA_NAME = "public"
DBT_PROJECT_NAME = "f1_race"
# the path where Cosmos will find the dbt executable (to find path,run: which dbt)
DBT_EXECUTABLE_PATH = "/home/airflow/.local/bin/dbt"
# The path to your dbt root directory
DBT_ROOT_PATH = "/usr/local/airflow/dbt"


@dag(
    start_date=datetime(2023, 6, 1),
    schedule=None,
    catchup=False,
)
def f1_dbt_transform():
    DbtTaskGroup(
        group_id="transform_data",
        dbt_project_name=DBT_PROJECT_NAME,
        conn_id=CONNECTION_ID,
        dbt_root_path=DBT_ROOT_PATH,
        dbt_args={
            "dbt_executable_path": DBT_EXECUTABLE_PATH,
            "schema": SCHEMA_NAME,
            "vars": '{"my_name": "ebuka"}',
        },
    )
transform = f1_dbt_transform()

transform 

