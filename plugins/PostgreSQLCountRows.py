#!/usr/bin/env python

from airflow.plugins_manager import AirflowPlugin
from airflow.operators import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow.hooks.postgres_hook import PostgresHook

class PostgreSQLCountRowsOperator(BaseOperator):
    '''
    Count rows in specified PostgreSQL table.
    Database is defined via connection.

    param table:              Table co count rows in
    type table:               string
    param postgresql_conn_id: Connection ID for target table
    type postgresql_conn_id:  string
    '''
    name = 'PostgreSQLCountRowsOperator'
    template_fields = ['table']
    def __init__(
        self,
        postgresql_conn_id,
        table,
        *args,
        **kwargs):
        super().__init__(*args, **kwargs)
        self.table = table
        self.postgresql_conn_id = postgresql_conn_id

    def execute(self, context):
        hook = PostgresHook(self.postgresql_conn_id)
        sql = 'SELECT COUNT(*) FROM {0};'.format(self.table)
        self.log.info('About to count rows with following SQL: %s', sql)
        query = hook.get_first(sql)
        self.log.info('Query returned: %s', query)
        self.xcom_push(context=context, key='table_records_count', value=query[0])
        return query

class PostgreSQLCustomOperators(AirflowPlugin):
    name = 'PostgreSQLCountRows'
    operators = [PostgreSQLCountRowsOperator]
