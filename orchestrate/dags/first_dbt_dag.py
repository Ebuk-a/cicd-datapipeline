from pendulum import datetime

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from cosmos.task_group import DbtTaskGroup

with DAG(
    dag_id="extract_dag",
    start_date=datetime(2023, 6, 20),
    schedule="@daily",
    catchup= False
) as dag:

    e1 = EmptyOperator(task_id="ingestion_workflow")

    dbt_tg = DbtTaskGroup(
        group_id="dbt_tg",
        dbt_project_name="jaffle_shop",
        conn_id="postgres",
        dbt_args={
            "schema": "public",
        },
        dag=dag,
    )

    e2 = EmptyOperator(task_id="some_extraction")

    e1 >> dbt_tg >> e2