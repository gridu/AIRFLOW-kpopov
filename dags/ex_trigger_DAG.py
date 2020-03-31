#!/usr/bin/env python

from __future__ import print_function

import datetime

from airflow import DAG

from airflow.operators.python_operator import PythonOperator
from airflow.operators.dagrun_operator import TriggerDagRunOperator
from airflow.sensors.external_task_sensor import ExternalTaskSensor
from airflow.models import TaskInstance
from airflow.utils import timezone
from airflow.utils.db import provide_session

with DAG('gridu_parent_dag', schedule_interval=None, start_date=datetime.datetime(2020, 3, 25), catchup=False) as parent_dag:
    print_context_op = PythonOperator(
        task_id='print_context_task',
        python_callable=lambda **kwargs: print(kwargs),
        provide_context=True
        )

    child_exec_date = timezone.make_aware(datetime.datetime.now())

    record_exec_date_op = PythonOperator(
        task_id='record_exec_date_task',
        python_callable=lambda ds, **c: c['ti'].xcom_push(key='child_exec_date', value=child_exec_date.isoformat()),
        provide_context=True
        )

    print_exec_date_op = PythonOperator(
        task_id='print_exec_date_task',
        python_callable=lambda ds, **kwargs: print(kwargs['ti'].xcom_pull(task_ids='record_exec_date_task', key='child_exec_date')),
        provide_context=True
        )

    print_exec_date2_op = PythonOperator(
        task_id='print_exec_date2_task',
        python_callable=lambda ds, **kwargs: print(kwargs['ti'].xcom_pull(task_ids='record_exec_date_task', key='child_exec_date')),
        provide_context=True
        )

    dag_run_op = TriggerDagRunOperator(
        task_id='dag_trigger_task',
        trigger_dag_id='gridu_child_dag',
        execution_date="{{ ti.xcom_pull(task_ids='record_exec_date_task', key='child_exec_date') }}"
        )

    @provide_session
    def get_child_exec_date(dt, session=None):
        ti = session.query(TaskInstance).filter(
            TaskInstance.dag_id == 'gridu_parent_dag',
            TaskInstance.task_id == 'record_exec_date_task',
            TaskInstance.execution_date == dt
            ).first()
        string_dt = ti.xcom_pull(
            task_ids='record_exec_date_task',
            key='child_exec_date',
            dag_id='gridu_parent_dag')
        return timezone.parse(string_dt)

    dag_sensor_op = ExternalTaskSensor(
            task_id='dag_waiter_task',
            external_dag_id='gridu_child_dag',
            # execution_date_fn=lambda dt: child_exec_date, # lambda to return ex_dag_exec_date whatever is passed to it
            execution_date_fn=get_child_exec_date,
            poke_interval=20,
            )

    print_context_op >> record_exec_date_op >> print_exec_date_op >> print_exec_date2_op >> dag_run_op >> dag_sensor_op

with DAG('gridu_child_dag', schedule_interval=None, start_date=datetime.datetime(2020, 3, 25), catchup=False) as child_dag:
    print_context_op = PythonOperator(
        task_id='print_context_task',
        python_callable=lambda **kwargs: print(kwargs),
        provide_context=True
        )
