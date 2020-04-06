from __future__ import print_function

import airflow.macros
import random

from datetime import datetime
from airflow import DAG

from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import BranchPythonOperator
from airflow.operators.postgres_operator import PostgresOperator
from airflow.operators import PostgreSQLCountRowsOperator
from airflow.operators.bash_operator import BashOperator
from airflow.utils.trigger_rule import TriggerRule
from airflow.hooks.postgres_hook import PostgresHook

config = {
    'gridu_dag_1_2': {'schedule': None, 'start_date': datetime(2020, 3, 23), 'def_args': {'owner': 'airflow'}, 'def_params': {'table': 'dag_1_tbl'}},
    'gridu_dag_2_2': {'schedule': None, 'start_date': datetime(2020, 3, 23), 'def_args': {'owner': 'airflow'}, 'def_params': {'table': 'dag_2_tbl'}},
    'gridu_dag_3_2': {'schedule': None, 'start_date': datetime(2020, 3, 23), 'def_args': {'owner': 'airflow'}, 'def_params': {'table': 'dag_3_tbl'}}
    }

CONNECTION_ID='gridu_psql'

def check_table_exist(**kwargs):
    hook = PostgresHook(CONNECTION_ID)
    query = hook.get_first(
        sql="SELECT * FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '{0}'; ".format(kwargs['tbl']),

    )
    print(query)
    if query:
        return 'insert_new_row_task'
    return 'create_table_task'

# the below function has been replaced with custom PostgreSQLCountRowsOperator
#def get_records_count(**kwargs):
#    hook = PostgresHook(CONNECTION_ID)
#    query = hook.get_first(
#        sql='SELECT COUNT(*) FROM {0};'.format(kwargs['dag'].params['table']),
#    )
#    print(query)
#    kwargs['ti'].xcom_push(key='table_records_count', value=query[0])
#    return query

for dag_id, dag_params in config.items():
    with DAG(
        dag_id,
        schedule_interval=dag_params['schedule'],
        start_date=dag_params['start_date'],
        default_args=dag_params['def_args'],
        params=dag_params['def_params']
        ) as job_dag:
        print_op = PythonOperator(
            task_id='print_' + dag_id,
            op_args = ['{dag_id} start processing table: {table}'.format(dag_id=dag_id, table=job_dag.params['table'])],
            python_callable=print
        )

        user_print_op = BashOperator(
            task_id='run_user_print_task',
            bash_command='whoami',
            xcom_push=True
            )

        check_op = BranchPythonOperator(
            task_id='table_check_task',
            python_callable=check_table_exist,
            op_kwargs={
                'tbl': job_dag.params['table']
                }
            )

        create_table_op = PostgresOperator(
            task_id='create_table_task',
            postgres_conn_id=CONNECTION_ID,
            autocommit=True,
            database='gridu',
            sql='CREATE TABLE {{ params.table }}(custom_id integer NOT NULL, user_name VARCHAR (50) NOT NULL, timestamp TIMESTAMP NOT NULL);'
            )

        insert_op = PostgresOperator(
            task_id='insert_new_row_task',
            trigger_rule=TriggerRule.NONE_FAILED,
            postgres_conn_id=CONNECTION_ID,
            database='gridu',
            sql='''INSERT INTO {{ params.table }} VALUES ({{ params.custom_id_value }}, '{{ ti.xcom_pull(task_ids='run_user_print_task', key='return_value') }}', '{{ macros.datetime.now().isoformat() }}');''',
            params={
                'custom_id_value': random.randint(100000,999999)
                }
            )

# the below operator has been replaced with custom PostgreSQLCountRowsOperator
#        query_op = PythonOperator(
#            task_id='query_the_table_task',
#            python_callable=get_records_count,
#            provide_context=True
#            )
        query_op = PostgreSQLCountRowsOperator(
            task_id='query_the_table_task',
            postgresql_conn_id=CONNECTION_ID,
            table='{{params.table}}'
            )

        push_result_op = PythonOperator(
            task_id='push_result_xcom',
            python_callable=lambda **kwargs: kwargs['ti'].xcom_push(
                key='result',
                value=kwargs['dag_run'].run_id + ' ended'),
            provide_context=True
        )

        print_op >> user_print_op >> check_op >> create_table_op >> insert_op >> query_op >> push_result_op
        check_op >> insert_op

        globals()[dag_id] = job_dag
