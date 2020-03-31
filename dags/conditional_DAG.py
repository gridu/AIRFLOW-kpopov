#!/usr/bin/env python

from __future__ import print_function

from datetime import datetime
from airflow import DAG

from airflow.operators.python_operator import PythonOperator
from airflow.operators.python_operator import BranchPythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.trigger_rule import TriggerRule

with DAG('gridu_conditional', schedule_interval=None, start_date=datetime(2020, 3, 24)) as dag:
    def minute_check():
        if int(datetime.now().minute) % 2:
            return 'minute_odd_task'
        return 'minute_even_task'

    condition_op = BranchPythonOperator(
        task_id='branch_task',
        python_callable=minute_check
        )

    minute_tasks_list = []
    for tsk in ['minute_odd_task', 'minute_even_task']:
        minute_tasks_list.append(DummyOperator(task_id=tsk))

    final_op = PythonOperator(
        task_id='final_task',
        python_callable=print,
        op_args=['Reached final task'],
        trigger_rule=TriggerRule.ONE_SUCCESS
        )

    condition_op >> minute_tasks_list >> final_op

