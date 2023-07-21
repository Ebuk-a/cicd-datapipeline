from airflow import DAG
from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from cosmos.task_group import DbtTaskGroup

from pandas import json_normalize
from datetime import datetime
import json
from urllib.request import urlopen
import pandas as pd
import requests

CONNECTION_ID = "postgres_default"
DB_NAME = "postgres"
SCHEMA_NAME = "public"
DBT_PROJECT_NAME = "f1_race"
# the path where Cosmos will find the dbt executable (to find path,run: which dbt)
DBT_EXECUTABLE_PATH = "/home/airflow/.local/bin/dbt"
# The path to your dbt root directory
DBT_ROOT_PATH = "/usr/local/airflow/dbt"
# CONNECTION_ID = "postgres_aws"
default_args = {"start_date": datetime(2023, 7, 1)}
params= {
        'limit': 1000,
        'format': json,
        'offset': 0,
        }
limit= 1000
offset= 0
payload = {}
headers = {}
_etl_loaded_at= datetime.now().strftime("%Y-%m-%d %H:%M:%S")
years = [2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]


@dag(schedule="@daily", default_args=default_args, catchup=False)
def f1_taskflow_dag():
    '''Race Results'''
    @task(task_id="extract_races")
    def _extract_races():
        races= pd.DataFrame(columns=['number', 'position', 'positionText', 'points', 'grid', 'laps',
        'status', 'Driver.driverId', 'Driver.permanentNumber', 'Driver.code',
        'Driver.url', 'Driver.givenName', 'Driver.familyName',
        'Driver.dateOfBirth', 'Driver.nationality', 'Constructor.constructorId',
        'Constructor.url', 'Constructor.name', 'Constructor.nationality',
        'Time.millis', 'Time.time', 'FastestLap.rank', 'FastestLap.lap',
        'FastestLap.Time.time', 'FastestLap.AverageSpeed.units',
        'FastestLap.AverageSpeed.speed', 'season', 'round', 'raceName',
        'Circuit.circuitId', 'date', 'time'])
        for year in years:
            print(year)
            url = "http://ergast.com/api/f1/{year}/results.json?limit={limit}&offset={offset}".format(year=year,limit= limit,offset= offset)
            response = requests.request("GET", url, headers=headers, data=payload)
            race_str = response.json()['MRData']['RaceTable']['Races']
            race = pd.json_normalize(race_str, record_path =['Results'], 
                                    meta= [
                                        'season', 'round', 'raceName', ['Circuit', 'circuitId'], 'date', 'time'
                                        ])
            races= pd.concat([races, race], ignore_index=True)

            #add a column _etl_loaded_at 
            races['_etl_loaded_at']= _etl_loaded_at
        print ('count of source races data is ' + str(races.shape[0]))
        return races
        
    @task(task_id="transform_races")
    def _transform_races(races):
        races["datetime_utc"] = races["date"] + ' ' +races["time"]
        fact_races_result= races[['Driver.driverId','Constructor.constructorId', 'raceName', 'season', 'round', 'Circuit.circuitId', 
                                'number', 'position', 'positionText', 'points', 'grid', 'laps','status',  'Time.millis', 'Time.time', 
                                'FastestLap.rank', 'FastestLap.lap','FastestLap.AverageSpeed.speed', 'datetime_utc', '_etl_loaded_at']]

        fact_races_result.rename(columns={'Driver.driverId': 'driver_id', 'Constructor.constructorId': 'constructor_id', 'raceName': 'race_name',
                                    'Circuit.circuitId': 'circuit_id', 'Time.millis': 'time_millis', 'Time.time': 'time_time', 'positionText':'position_text',
                                    'FastestLap.rank': 'fastest_lap_rank', 'FastestLap.lap': 'fastest_lap', 'FastestLap.AverageSpeed.speed': 'fastest_lap_avg_speed'}, inplace=True)

        fact_races_result[['datetime_utc', '_etl_loaded_at']]= fact_races_result[['datetime_utc', '_etl_loaded_at']].apply(pd.to_datetime, format='%Y-%m-%d %H:%M:%S')

        convert_dict = {'round': int,
                        'points': float, 
                        'laps': int, 
                        'time_millis': float, 
                        'fastest_lap_avg_speed': float, 
                        }
        fact_races_result = fact_races_result.astype(convert_dict)
        print ('count of transformed fact races data is '+ str(fact_races_result.shape[0]))
        return fact_races_result

    @task(task_id="store_races")
    def _store_races(fact_races_result):
        hook = PostgresHook(conn_id= CONNECTION_ID)
        fact_races_result.to_sql('raw_races_result', con= hook.get_sqlalchemy_engine(), schema='public', if_exists='replace', 
                                method='multi', chunksize= 1000, index= False)
        
    '''Constructors'''
    @task(task_id="extract_constructors")
    def _extract_constructors():
        url = "http://ergast.com/api/f1/constructors.json?limit={limit}&offset={offset}".format(limit=limit,offset=offset)
        response = requests.request("GET", url, headers=headers, data=payload)
        constructors_str = response.json()['MRData']['ConstructorTable']
        constructors = pd.json_normalize(constructors_str, record_path =['Constructors'])
        constructors['_etl_loaded_at']= _etl_loaded_at
        # print ('count of source constructors data is ' + str(constructors.shape[0]))
        return constructors
        
    @task(task_id="transform_constructors")
    def _transform_constructors(constructors):
        constructors[['_etl_loaded_at']]= constructors[['_etl_loaded_at']].apply(pd.to_datetime, format='%Y-%m-%d %H:%M:%S')
        constructors.rename(columns={'constructorId': 'constructor_id'
                                        }, inplace=True)
        # print ('count of transformed fact constructors data is '+ str(constructors.shape[0]))
        return constructors

    @task(task_id="store_constructors")
    def _store_constructors(constructors):
        hook = PostgresHook(conn_id= CONNECTION_ID)
        constructors.to_sql('raw_constructors', con= hook.get_sqlalchemy_engine(), schema='public', if_exists='replace', 
                                method='multi', chunksize= 1000, index= False)

    '''Schedules'''
    @task(task_id="extract_schedules")
    def _extract_schedules():
        schedules= pd.DataFrame(columns=['season', 'round', 'url', 'raceName', 'date', 'time',
            'Circuit.circuitId', 'Circuit.url', 'Circuit.circuitName',
            'Circuit.Location.lat', 'Circuit.Location.long',
            'Circuit.Location.locality', 'Circuit.Location.country',
            'FirstPractice.date', 'FirstPractice.time', 'SecondPractice.date',
            'SecondPractice.time', 'ThirdPractice.date', 'ThirdPractice.time',
            'Qualifying.date', 'Qualifying.time', 'Sprint.date', 'Sprint.time']
            )
        for year in years:
            url = "http://ergast.com/api/f1/{year}.json?limit={limit}&offset={offset}".format(year= year, limit= limit, offset= offset)
            response = requests.request("GET", url, headers=headers, data=payload)
            schedule_str = response.json()['MRData']['RaceTable']
            schedule = pd.json_normalize(schedule_str, record_path =['Races'])
            schedules= pd.concat([schedules, schedule], ignore_index=True)

        schedules['_etl_loaded_at']= _etl_loaded_at
        return schedules
        
    @task(task_id="transform_schedules")
    def _transform_schedules(schedules):
        dim_schedules= schedules[['season', 'round', 'url', 'raceName', 'date', 'time',
            'Circuit.circuitId','FirstPractice.date', 'FirstPractice.time', 'SecondPractice.date',
            'SecondPractice.time', 'ThirdPractice.date', 'ThirdPractice.time',
            'Qualifying.date', 'Qualifying.time', 'Sprint.date', 'Sprint.time',
            '_etl_loaded_at']]

        #Combine date and time columns into single columns
        dim_schedules["first_practice_datetime"] = dim_schedules["FirstPractice.date"] + ' ' + dim_schedules["FirstPractice.time"]
        dim_schedules["second_practice_datetime"] = dim_schedules["SecondPractice.date"] + ' ' + dim_schedules["SecondPractice.time"]
        dim_schedules["third_practice_datetime"] = dim_schedules["ThirdPractice.date"] + ' ' + dim_schedules["ThirdPractice.time"]
        dim_schedules["qualifying_datetime"] = dim_schedules["Qualifying.date"] + ' ' + dim_schedules["Qualifying.time"]
        dim_schedules["sprint_datetime"] = dim_schedules["Sprint.date"] + ' ' + dim_schedules["Sprint.time"]
        dim_schedules["datetime"] = dim_schedules["date"] + ' ' + dim_schedules["time"]

        #select columns (ignore the unmerged date and times)
        dim_schedules= dim_schedules.loc[:, ~dim_schedules.columns.isin(['date', 'time', 'FirstPractice.date', 'FirstPractice.time', 'SecondPractice.date',
                                                        'SecondPractice.time', 'ThirdPractice.date', 'ThirdPractice.time','Qualifying.date', 
                                                        'Qualifying.time', 'Sprint.date', 'Sprint.time',])]

        #rename column(s)
        dim_schedules.rename(columns={'Circuit.circuitId': 'circuit_id',
                                      'raceName':'race_name'
                                        }, inplace=True)

        #reorder columns
        dim_schedules= dim_schedules[['datetime','season', 'round', 'url', 'race_name', 'circuit_id','first_practice_datetime', 
                                    'second_practice_datetime','third_practice_datetime', 'qualifying_datetime', 'sprint_datetime', '_etl_loaded_at']]

        #convert the datetime columns from object to datetime type.
        dim_schedules[['datetime','first_practice_datetime', 'second_practice_datetime',
               'third_practice_datetime', 'qualifying_datetime', 
               'sprint_datetime', '_etl_loaded_at']]= dim_schedules[['datetime','first_practice_datetime', 'second_practice_datetime',
                                                                    'third_practice_datetime', 'qualifying_datetime', 
                                                                    'sprint_datetime', '_etl_loaded_at']].apply(pd.to_datetime, format='%Y-%m-%d %H:%M:%S')
        #convert the round column to int
        convert_dict = {'round': int}
        dim_schedules = dim_schedules.astype(convert_dict)

        return dim_schedules

    @task(task_id="store_schedules")
    def _store_schedules(schedules):
        hook = PostgresHook(conn_id= CONNECTION_ID)
        schedules.to_sql('raw_schedules', con= hook.get_sqlalchemy_engine(), schema='public', if_exists='replace', 
                                method='multi', chunksize= 1000, index= False)
    '''Seasons'''
    @task(task_id="extract_seasons")
    def _extract_seasons():
        url = "http://ergast.com/api/f1/seasons.json?limit={limit}".format(limit= limit)
        response = requests.request("GET", url, headers=headers, data=payload)
        season_str = response.json()['MRData']['SeasonTable']
        season = pd.json_normalize(season_str, record_path =['Seasons'])
        season['_etl_loaded_at']= _etl_loaded_at

        return season
        
    @task(task_id="transform_seasons")
    def _transform_seasons(season):
        season[['_etl_loaded_at']]= season[['_etl_loaded_at']].apply(pd.to_datetime, format='%Y-%m-%d %H:%M:%S')
        return season

    @task(task_id="store_seasons")
    def _store_seasons(season):
        hook = PostgresHook(conn_id= CONNECTION_ID)
        season.to_sql('raw_seasons', con= hook.get_sqlalchemy_engine(), schema='public', if_exists='replace', 
                                method='multi', chunksize= 1000, index= False)

    @task(task_id="extract_drivers")
    def _extract_drivers():
        url = "http://ergast.com/api/f1/drivers.json"
        response = requests.get(url, params= params)
        drivers_data = response.json()['MRData']['DriverTable']
        drivers = pd.json_normalize(drivers_data, record_path =['Drivers'])
        drivers['_etl_loaded_at']= _etl_loaded_at

        return drivers
        
    @task(task_id="transform_drivers")
    def _transform_drivers(drivers):
        drivers[['_etl_loaded_at']]= drivers[['_etl_loaded_at']].apply(pd.to_datetime, format='%Y-%m-%d %H:%M:%S')
        drivers[['dateOfBirth']]= drivers[['dateOfBirth']].apply(pd.to_datetime, format='%Y-%m-%d')

        drivers.rename(columns={'driverId': 'driver_id', 'givenName': 'given_name', 'familyName': 'family_name','dateOfBirth': 'date_of_birth',
                                'permanentNumber': 'permanent_number'
                                        }, inplace=True)
        return drivers

    @task(task_id="store_drivers")
    def _store_drivers(drivers):
        hook = PostgresHook(conn_id= CONNECTION_ID)
        drivers.to_sql('raw_drivers', con= hook.get_sqlalchemy_engine(), schema='public', if_exists='replace', 
                                method='multi', chunksize= 1000, index= False)
        
    @task(task_id="extract_circuits")
    def _extract_circuits():
        circuits= pd.DataFrame(columns=['circuitId', 'url', 'circuitName', 'Location.lat', 'Location.long',
       'Location.locality', 'Location.country', 'season'])


        circuit_url = "http://ergast.com/api/f1/circuits.json?limit={limit}&offset={offset}".format(limit= limit,offset= offset)

        circuit_response = requests.request("GET", circuit_url, headers=headers, data=payload)

        circuit_str = circuit_response.json()['MRData']['CircuitTable']

        circuits = pd.json_normalize(circuit_str, record_path =['Circuits']
                    )
        circuits['_etl_loaded_at']= _etl_loaded_at

        return circuits
        
    @task(task_id="transform_circuits")
    def _transform_circuits(circuits):
        #update datatypes
        dim_circuits= circuits.astype({'Location.long': float, 'Location.lat': float})
        dim_circuits[['_etl_loaded_at']]= dim_circuits[['_etl_loaded_at']].apply(pd.to_datetime, format='%Y-%m-%d %H:%M:%S')

        #create the cordinate point using longitude and latitude
        # dim_circuits['circuitLocationPoint'] = [Point(xy) for xy in zip(dim_circuits['Location.long'], dim_circuits['Location.lat'])] 

        #rename column(s)
        dim_circuits.rename(columns={'circuitId': 'circuit_id', 'circuitName': 'circuit_name', 'Location.lat': 'location_lat','Location.long': 'location_long',
                                    'Location.locality': 'location_locality', 'Location.country': 'location_country'
                                        }, inplace=True)
        #select columns
        dim_circuits= dim_circuits[['circuit_id', 'url', 'circuit_name', 'location_lat', 'location_long',
                                    'location_locality', 'location_country', '_etl_loaded_at',
                                    ]]
        return dim_circuits

    @task(task_id="store_circuits")
    def _store_circuits(circuits):
        hook = PostgresHook(conn_id= CONNECTION_ID)
        circuits.to_sql('raw_circuits', con= hook.get_sqlalchemy_engine(), schema='public', if_exists='replace', 
                                method='multi', chunksize= 1000, index= False)
    
    f1_dbt_transform= DbtTaskGroup(
        group_id="dbt_transform_data",
        dbt_project_name=DBT_PROJECT_NAME,
        conn_id=CONNECTION_ID,
        dbt_root_path=DBT_ROOT_PATH,
        dbt_args={
            "dbt_executable_path": DBT_EXECUTABLE_PATH,
            "schema": SCHEMA_NAME,
            "vars": '{"my_name": "ebuka"}',
        },
    )

    [_store_races(_transform_races(_extract_races())), _store_constructors(_transform_constructors(_extract_constructors())) 
    ,_store_schedules(_transform_schedules(_extract_schedules())), _store_seasons(_transform_seasons(_extract_seasons()))
    ,_store_drivers(_transform_drivers(_extract_drivers())), _store_circuits(_transform_circuits(_extract_circuits()))] >> f1_dbt_transform

    

f1_taskflow_dag() 