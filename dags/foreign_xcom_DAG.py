#!/usr/bin/env python

from __future__ import print_function

import pytz
import datetime

from airflow import DAG

from airflow.operators.python_operator import PythonOperator
from airflow.models import XCom
from airflow.settings import TIMEZONE

with DAG('gridu_foreign_xcom', schedule_interval=None, start_date=datetime.datetime(2020, 3, 24), catchup=False) as dag:
    def write_xcom():
        XCom.set(
            key='injected',
            value='overwrite',
            task_id='query_the_table_dag_1_db',
            dag_id='gridu_dag_1_2',
            execution_date=datetime.datetime(2020, 3, 25, 9, 44, 29, 937856, tzinfo=pytz.utc)
#            execution_date=pytz.timezone('UTC').utc_timezone.localize(datetime.strptime('2020-03-25T09:44:29.937856+00:00'.replace("T", " "),'%Y-%m-%d %H:%M:%S.%f'))
            )

    write_op = PythonOperator(
        task_id='foreign_writer',
        python_callable=write_xcom,
        )
