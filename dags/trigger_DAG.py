from datetime import datetime

from airflow import DAG

from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from airflow.contrib.sensors.file_sensor import FileSensor
from airflow.operators.dagrun_operator import TriggerDagRunOperator
from airflow.sensors.external_task_sensor import ExternalTaskSensor
from airflow.operators.subdag_operator import SubDagOperator
from airflow.models import Variable

FILE_WATCH_VARIABLE = 'file_to_watch'
DAG_TO_TRIGGER = 'gridu_dag_1_2'

def awaiter_subdag(subdag_name, ex_dag_id):
    def print_xcom_result(**kwargs):
        result = kwargs['ti'].xcom_pull(
            # include_prior_dates=True,
            key='result',
            dag_id=ex_dag_id,
            task_ids='push_result_xcom'
            )
        print('Result of subdag is {0}'.format(result))
        print("Full context below:\n{0}".format(kwargs))

    new_sub_dag =  DAG(
        subdag_name,
        schedule_interval=None,
        start_date=datetime(2020, 3, 25),
        catchup=False
        )

    dag_sensor_op = ExternalTaskSensor(
            task_id='dag_waiter_task',
            external_dag_id=ex_dag_id,
            poke_interval=20,
            dag=new_sub_dag
            )

    print_result_op = PythonOperator(
        task_id='print_subdag_result',
        python_callable=print_xcom_result,
        provide_context=True,
        dag=new_sub_dag
        )

    file_clean_op = BashOperator(
        task_id='file_clean_task',
        bash_command='rm -v  "{{{{ var.value.{0} }}}}"'.format(FILE_WATCH_VARIABLE),
        dag=new_sub_dag
        )

    finish_flag_op = BashOperator(
        task_id='finish_flag_task',
        bash_command='touch "/tmp/{{ ts_nodash }}"',
        dag=new_sub_dag
        )

    dag_sensor_op >> print_result_op >> file_clean_op >> finish_flag_op
    return new_sub_dag

with DAG('gridu_trigger_dag', schedule_interval=None, start_date=datetime(2020, 3, 25), catchup=False) as dag:
    file_sensor_op = FileSensor(
        task_id='file_sensor_task',
        filepath=Variable.get(FILE_WATCH_VARIABLE), # default_var= not set to cause Exception if variable not defined
        poke_interval=10,
        timeout=180,
        queue='filesensor' # needed to know which node to place the file to
        )

    dag_run_op = TriggerDagRunOperator(
        task_id='dag_trigger_task',
        trigger_dag_id=DAG_TO_TRIGGER,
        execution_date='{{ execution_date }}'
        )

    sub_dag_op = SubDagOperator(
        task_id='awaiter_subdag',
        subdag=awaiter_subdag(
            subdag_name='{0}.awaiter_subdag'.format(dag.dag_id),
            ex_dag_id=DAG_TO_TRIGGER
            )
        )

    file_sensor_op >> dag_run_op >> sub_dag_op

