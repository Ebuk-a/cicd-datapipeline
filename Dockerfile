FROM apache/airflow:2.6.1

WORKDIR "/usr/local/airflow"
USER root
RUN sudo apt-get -y update
RUN chown -R airflow:root /usr/local/airflow

USER airflow

RUN python -m pip install --upgrade pip

COPY requirements/* ./

RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r airflow-requirements.txt
# RUN pip install --no-cache-dir -r airflow-requirements.txt

RUN id airflow

# Create a virtual env for dbt and install dbt requirements to avoid depency conflicts with airflow.
RUN whoami && ls -la && python3 -m venv --system-site-packages dbt_venv

RUN whoami && ls -la
RUN source dbt_venv/bin/activate && pip3 install --no-cache-dir -r dbt-requirements.txt

WORKDIR "/opt/airflow" 
COPY orchestrate/* ./dags


