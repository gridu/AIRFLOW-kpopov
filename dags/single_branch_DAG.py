#!/usr/bin/env python

from __future__ import print_function

from datetime import datetime
from airflow import DAG

from airflow.operators.python_operator import PythonOperator
from airflow.operators.python_operator import BranchPythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.trigger_rule import TriggerRule

with DAG('gridu_single_branch', schedule_interval=None, start_date=datetime(2020, 3, 24)) as dag:
    def minute_check():
        if int(datetime.now().minute) % 2:
            return 'minute_odd_task'
        return 'final_task'

    condition_op = BranchPythonOperator(
        task_id='branch_task',
        python_callable=minute_check
        )

    minute_odd_op = DummyOperator(task_id='minute_odd_task')

    final_op = PythonOperator(
        task_id='final_task',
        python_callable=print,
        op_args=['Reached final task'],
        trigger_rule=TriggerRule.ONE_SUCCESS
        )

    condition_op >> minute_odd_op >> final_op
    condition_op >> final_op


