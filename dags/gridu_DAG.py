#!/usr/bin/env python

from datetime import datetime
from airflow import DAG

default_args = {
  'owner': 'kpopov',
  'start_date': datetime(2020, 3, 23)
}

with DAG('gridu_dag', default_args=default_args, schedule_interval='@once') as dag:
  pass
